"""
Programmatic extensions for assembled OEMetadata dictionaries.

This module exposes a lightweight, schema-agnostic builder that lets code
augment an already assembled OEMetadata mapping without touching the YAML
authoring files. Typical pipeline use cases:

- inject runtime values (e.g., publicationDate),
- append contributors (dataset- or resource-level) with de-duplication,
- add or refine field descriptions,
- merge dicts/lists at JSONPointer-like paths,
- schema-driven hygiene: ensure required keys, prune empty values.

The builder mutates an internal deep copy of the input; call ``build()`` to
retrieve the final dict (optionally validated).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from typing import Literal, Optional

from omi.base import get_metadata_specification
from omi.creation.cleaner import (
    detect_unknown_keys,
    lint_metadata_against_schema,
    normalize_metadata_for_schema,
    strip_unknown_keys,
)
from omi.validation import validate_metadata

Json = dict[str, object]


class SchemaDriftError(Exception):
    """Raised when strict schema validation fails due to database vs. YAML drift."""


# -----------------------------------------------------------------------------
# Policy types
# -----------------------------------------------------------------------------

CreatePolicy = Literal["never", "dicts"]
OverwritePolicy = Literal["always", "if_absent"]
ListStrategy = Literal["concat", "replace", "dedupe"]
ValidatePolicy = Literal["validate", "skip"]
LicensePolicy = Literal["check", "skip"]


# -----------------------------------------------------------------------------
# Internal: JSON-pointer resolution
# -----------------------------------------------------------------------------


def _resolve_pointer(
    root: object,
    pointer: str,
    *,
    create: bool | None = None,
) -> tuple[object | None, str]:
    """
    Resolve a JSONPointer-like path and return (parent, final_key).

    Supports simple slash-separated paths into dicts/lists (e.g., ``/a/b/0``).

    Parameters
    ----------
    root :
        Root JSON-like structure (dict/list/scalars).
    pointer :
        Path to resolve. Use ``/``-separated segments; list indices may be
        addressed with integers (e.g., ``/resources/0/schema``).
    create :
        If True, missing dict segments along the path are created.

    Returns
    -------
    tuple[object | None, str]
        A pair ``(parent, final_key)`` where ``parent[final_key]`` is the target.
        If the pointer refers to the root itself (``""`` or ``"/"``), returns
        ``(None, "")``.

    Raises
    ------
    KeyError
        If a required path component is missing and ``create`` is False.
    IndexError
        If a list index segment is out of bounds.
    TypeError
        If traversal encounters a non-container where a dict/list is required.
    ValueError
        If a list index segment cannot be parsed as an integer.
    """
    if pointer == "" or pointer == "/":
        return None, ""

    parts = [p for p in pointer.split("/") if p != ""]
    cur = root
    for part in parts[:-1]:
        if isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError as exc:
                raise ValueError(f"List index segment must be an integer, got '{part}'.") from exc
            if idx < 0 or idx >= len(cur):
                raise IndexError(f"List index {idx} out of range at segment '{part}'.")
            cur = cur[idx]
        elif isinstance(cur, dict):
            if part not in cur:
                if create:
                    cur[part] = {}
                else:
                    raise KeyError(f"Missing path component: '{part}' in '{pointer}'.")
            cur = cur[part]
        else:
            raise TypeError(f"Cannot traverse into {type(cur).__name__} at segment '{part}'.")
    return cur, parts[-1]


def _ensure_dict_target(
    parent: object,
    key: str,
    path: str,
    *,
    create_flag: bool,
) -> dict[str, object]:
    """
    Ensure the value at parent[key] is a dict, creating it if allowed.

    Returns the dict to be used as merge target.
    """
    if isinstance(parent, list):
        idx = int(key)
        if not isinstance(parent[idx], dict):
            if create_flag:
                parent[idx] = {}
            else:
                msg = f"Target at '{path}' is not a dict."
                raise TypeError(msg)
        return parent[idx]

    if isinstance(parent, dict):
        if key not in parent or not isinstance(parent[key], dict):
            if create_flag:
                parent[key] = {}
            else:
                msg = f"Target at '{path}' is not a dict."
                raise TypeError(msg)
        return parent[key]

    msg = f"Target parent at '{path}' is not a list or mapping."
    raise TypeError(msg)


def _merge_into_target(  # noqa: PLR0913
    builder: MetadataBuilder,
    target: dict[str, object],
    path: str,
    key: str,
    value: object,
    create_policy: CreatePolicy,
    overwrite_policy: OverwritePolicy,
) -> None:
    """Merge a single key/value pair into target according to policies."""
    if key in target and isinstance(target[key], dict) and isinstance(value, dict):
        # delegate nested dict merge back to the builder
        builder.merge_dict(
            f"{path}/{key}",
            value,
            create_policy=create_policy,
            overwrite_policy=overwrite_policy,
        )
    elif overwrite_policy == "always" or key not in target:
        target[key] = deepcopy(value)


# -----------------------------------------------------------------------------
# Internal: schema-driven hygiene (ensure required, prune empty)
# -----------------------------------------------------------------------------

_EMPTY_SENTINELS: tuple[object, ...] = (None, "", [], {})


def _join_ptr(base: str, prop: str) -> str:
    return f"{base}/{prop}" if base else f"/{prop}"


def _collect_required_paths(schema: Mapping[str, object], base: str = "") -> set[str]:
    """
    Collect JSON-pointer paths for required object properties in a JSON Schema.

    Handles:
      - ``type: object`` with ``required`` and ``properties``
      - composition (``anyOf``/``oneOf``/``allOf``): union of branches' required paths
      - arrays: walks into ``items`` when present (records wildcard paths like ``/*/prop``)
    """
    paths: set[str] = set()

    # composition first: union is a safe over-approximation
    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema:
            for br in schema[key]:
                paths.update(_collect_required_paths(br, base))
            return paths

    t = schema.get("type")

    if t == "object":
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for prop in required:
            paths.add(_join_ptr(base, prop))
        for prop, p_schema in props.items():
            paths.update(_collect_required_paths(p_schema, _join_ptr(base, prop)))

    elif t == "array":
        items = schema.get("items")
        if isinstance(items, Mapping):
            paths.update(_collect_required_paths(items, f"{base}/*"))

    return paths


def _ensure_required_paths(obj: object, required_paths: set[str]) -> object:  # noqa: C901
    """
    Ensure all required paths exist in ``obj`` by creating missing dict keys with None.

    Only operates on object properties (dicts). For required paths that include an
    array wildcard (``/*/prop``), we attempt to set the property on each object element
    of the array if the array exists.
    """
    out = deepcopy(obj)

    # Group leaves by parent pointer: /a/b/c -> parent=/a/b, leaf=c
    parents: dict[str, list[str]] = {}
    for p in required_paths:
        if not p or p == "/":
            continue
        parts = [x for x in p.split("/") if x]
        parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else ""
        leaf = parts[-1]
        parents.setdefault(parent, []).append(leaf)

    def _walk_and_set(parent_ptr: str, leaves: list[str]) -> None:  # noqa: C901
        # wildcard support
        if "/*/" in parent_ptr or parent_ptr.endswith("/*"):
            parts = [x for x in parent_ptr.split("/") if x]

            def _recur(curr: object, idx: int) -> None:
                if idx >= len(parts):
                    if isinstance(curr, dict):
                        for leaf in leaves:
                            curr.setdefault(leaf, None)
                    return
                part = parts[idx]
                if part == "*":
                    if isinstance(curr, list):
                        for e in curr:
                            _recur(e, idx + 1)
                elif isinstance(curr, dict) and part in curr:
                    _recur(curr[part], idx + 1)

            _recur(out, 0)
            return

        # normal object parent
        if parent_ptr == "":
            parent = out
        else:
            parent = out
            for seg in [x for x in parent_ptr.split("/") if x]:
                if not isinstance(parent, dict):
                    return
                parent = parent.setdefault(seg, {})
        if isinstance(parent, dict):
            for leaf in leaves:
                parent.setdefault(leaf, None)

    for parent_ptr, leaves in parents.items():
        _walk_and_set(parent_ptr, leaves)

    return out


def _prune_empty(obj: object, required_paths: set[str], base: str = "") -> object:
    """Remove keys whose values are empty (None, '', [], {}) unless required."""

    def _is_required(path: str) -> bool:
        if path in required_paths:
            return True
        # keep parents of required children
        return any(rp.startswith(path + "/") for rp in required_paths)

    if isinstance(obj, dict):
        result: dict[str, object] = {}
        for k, v in obj.items():
            p = f"{base}/{k}"
            cleaned = _prune_empty(v, required_paths, p)
            if cleaned in _EMPTY_SENTINELS and not _is_required(p):
                continue
            result[k] = cleaned
        return result

    if isinstance(obj, list):
        return [_prune_empty(v, required_paths, f"{base}/*") for v in obj]

    return obj


# -----------------------------------------------------------------------------
# Resource scope
# -----------------------------------------------------------------------------


class _ResourceScope:
    """Fluent resource-scoped view that prefixes all paths with /resources/{i}."""

    def __init__(self, parent: MetadataBuilder, index: int) -> None:
        self._p = parent
        self._idx = index
        self._base = f"/resources/{index}"

    # -- relative path helpers --

    def _rel(self, rel_path: str) -> str:
        rel = rel_path[1:] if rel_path.startswith("/") else rel_path
        return f"{self._base}/{rel}" if rel else self._base

    # -- public API within resource --

    def set(self, rel_path: str, value: object, **kw) -> _ResourceScope:  # noqa: A003
        """Set a value relative to this resource (e.g. ``'context'`` or ``'/context'``)."""
        self._p.set_path(self._rel(rel_path), value, **kw)
        return self

    def merge_dict(self, rel_path: str, mapping: dict[str, object], **kw) -> _ResourceScope:
        """Deep-merge a mapping into a dict relative to this resource."""
        self._p.merge_dict(self._rel(rel_path), mapping, **kw)
        return self

    def merge_list(self, rel_path: str, values: Iterable[object], **kw) -> _ResourceScope:
        """Merge a list relative to this resource using a strategy (replace/concat/dedupe)."""
        self._p.merge_list(self._rel(rel_path), values, **kw)
        return self

    def merge_and_diff_db_schema(self, db_skeleton: dict[str, object], *, strict: bool = False) -> dict[str, object]:
        """
        Compare the YAML schema with the database schema.

        Updates structural types and reports (or fails) on schema drift.

        Parameters
        ----------
        db_skeleton : dict
            The resource dictionary generated by OMI's `inspect_db_table`.
        strict : bool
            If True, raises a SchemaDriftError if there are missing columns.

        Returns
        -------
        dict
            A report containing 'missing_in_yaml', 'missing_in_db', and 'type_mismatches'.
        """
        # Solves SLF001: Access via the new .metadata property
        resources = self._p.metadata.get("resources", [])
        if not isinstance(resources, list) or self._idx >= len(resources):
            return {"missing_in_yaml": [], "missing_in_db": [], "type_mismatches": {}}

        res = resources[self._idx]
        if not isinstance(res, dict):
            return {"missing_in_yaml": [], "missing_in_db": [], "type_mismatches": {}}

        yaml_schema = res.get("schema", {})
        if not isinstance(yaml_schema, dict):
            yaml_schema = {}
            res["schema"] = yaml_schema

        yaml_fields = yaml_schema.get("fields", [])
        if not isinstance(yaml_fields, list):
            yaml_fields = []

        db_schema = db_skeleton.get("schema", {})
        if not isinstance(db_schema, dict):
            db_schema = {}
        db_fields = db_schema.get("fields", [])
        if not isinstance(db_fields, list):
            db_fields = []

        yaml_dict = {f["name"]: f for f in yaml_fields if isinstance(f, dict) and "name" in f}
        db_dict = {f["name"]: f for f in db_fields if isinstance(f, dict) and "name" in f}

        # Extracted calculation to lower complexity
        diff_report = self._compute_schema_diff(yaml_dict, db_dict)

        if strict and (diff_report["missing_in_yaml"] or diff_report["missing_in_db"]):
            raise SchemaDriftError(
                f"Schema drift detected in resource '{res.get('name')}':\n"
                f"Missing in DB (dropped?): {diff_report['missing_in_db']}\n"
                f"Missing in YAML (undocumented?): {diff_report['missing_in_yaml']}",
            )

        # Extracted merge logic to lower complexity
        missing_in_db = [str(x) for x in diff_report.get("missing_in_db", [])]
        yaml_schema["fields"] = self._merge_schema_fields(yaml_dict, db_dict, missing_in_db)

        if "primaryKey" in db_schema:
            yaml_schema["primaryKey"] = deepcopy(db_schema["primaryKey"])

        return diff_report

    def _compute_schema_diff(
        self,
        yaml_dict: dict[str, dict[str, object]],
        db_dict: dict[str, dict[str, object]],
    ) -> dict[str, object]:
        """Calculate structural diff between YAML and DB fields."""
        yaml_keys = set(yaml_dict.keys())
        db_keys = set(db_dict.keys())

        type_mismatches = {}
        for col in yaml_keys & db_keys:
            y_type = yaml_dict[col].get("type")
            d_type = db_dict[col].get("type")
            if y_type and d_type and y_type != d_type:
                type_mismatches[col] = {"yaml": y_type, "db": d_type}

        return {
            "missing_in_yaml": list(db_keys - yaml_keys),
            "missing_in_db": list(yaml_keys - db_keys),
            "type_mismatches": type_mismatches,
        }

    def _merge_schema_fields(
        self,
        yaml_dict: dict[str, dict[str, object]],
        db_dict: dict[str, dict[str, object]],
        missing_in_db: list[str],
    ) -> list[dict[str, object]]:
        """Apply DB schema structures over YAML, preserving YAML descriptions."""
        merged_fields = []

        for db_col_name, db_field in db_dict.items():
            if db_col_name in yaml_dict:
                combined = deepcopy(yaml_dict[db_col_name])
                combined["type"] = db_field.get("type", combined.get("type"))
                if "nullable" in db_field:
                    combined["nullable"] = db_field["nullable"]
                merged_fields.append(combined)
            else:
                new_field = deepcopy(db_field)
                new_field["description"] = "TODO: Description missing in YAML metadata"
                merged_fields.append(new_field)

        # Solves PERF401: Uses list comprehension for transformation
        merged_fields.extend([yaml_dict[col] for col in missing_in_db])

        return merged_fields

    def append_contributor(self, contributor: dict[str, object], *, dedupe_on: str = "title") -> _ResourceScope:
        """Append a contributor to this resource's ``contributors`` (de-duplicated)."""

        def _key(x: object) -> object:
            return x.get(dedupe_on) if isinstance(x, dict) else repr(x)

        self.merge_list("contributors", [contributor], strategy="dedupe", key=_key)
        return self

    def set_field_descriptions(
        self,
        descriptions: dict[str, str],
        *,
        default_nullable: bool | None = None,
    ) -> _ResourceScope:
        """Set schema field descriptions (and optionally default ``nullable``) on this resource."""
        self._p.set_field_descriptions_for_index(
            self._idx,
            descriptions,
            default_nullable=default_nullable,
        )
        return self

    def done(self) -> MetadataBuilder:
        """Return to the root builder."""
        return self._p


# -----------------------------------------------------------------------------
# Builder
# -----------------------------------------------------------------------------


class MetadataBuilder:
    """
    Lightweight, schema-agnostic builder to mutate assembled OEMetadata dicts.

    Features
    --------
    - Path-based set/merge operations (dicts and lists) using explicit policies.
    - Resource scoping: ``.resource('name').append_contributor({...}).done()``.
    - Convenience helpers (contributors, field descriptions).
    - Schema-driven hygiene: ``ensure_required`` and ``prune_empty``.
    - Optional validation via :func:`omi.validation.validate_metadata` in ``build()``.

    Notes
    -----
    The builder keeps a deep copy of the input mapping; original metadata is not
    modified. Methods return ``self`` for fluent chaining.
    """

    def __init__(self, metadata: Json, oem_version: Optional[str] = None) -> None:
        """
        Initialize with an OEMetadata mapping.

        Parameters
        ----------
        metadata :
            Already-assembled OEMetadata dictionary.
        oem_version :
            If provided, the corresponding specification is loaded (kept for
            potential future helpers; not required for core operations).
        """
        self._md: Json = deepcopy(metadata)
        self._oem_version = oem_version
        self._oem_spec = get_metadata_specification(oem_version) if oem_version else None
        self._concat_list_keys: set[str] = {"keywords", "topics", "languages"}

    @property
    def metadata(self) -> Json:
        """Expose the internal metadata dict for scoped operations."""
        return self._md

    # ---------- Low-level path operations ----------

    def set_path(
        self,
        path: str,
        value: object,
        *,
        create_policy: CreatePolicy = "dicts",
        # backward-compat shim (deprecated): if someone passes create=..., map it
        **deprecated_bool: object,
    ) -> MetadataBuilder:
        """
        Set a value at *path* (JSONPointer-like), per the create policy.

        Parameters
        ----------
        path :
            Slash-separated navigation path (e.g., ``/resources/0/title``).
        value :
            Value to assign at the target location.
        create_policy :
            - ``"dicts"``: create missing dict segments,
            - ``"never"``: do not create, raise if missing.
            Default is ``"dicts"``.
        deprecated_bool :
            Backwards-compat shim, accepting legacy boolean keyword arguments
            such as ``create=...``. Prefer using ``create_policy`` instead.
        """
        if "create" in deprecated_bool:  # type: ignore[truthy-bool]
            create_policy = "dicts" if bool(deprecated_bool["create"]) else "never"

        create_flag = create_policy == "dicts"
        parent, key = _resolve_pointer(self._md, path, create=create_flag)
        if parent is None:
            if key in ("", "/"):
                self._md = value  # replace root
            else:
                msg = "Invalid root replacement request."
                raise ValueError(msg)
            return self

        if isinstance(parent, list):
            idx = int(key)
            parent[idx] = value
        elif isinstance(parent, dict):
            parent[key] = value
        else:
            raise TypeError(f"Target parent at '{path}' is not indexable/mapping.")
        return self

    def merge_dict(
        self,
        path: str,
        mapping: dict[str, object],
        *,
        create_policy: CreatePolicy = "dicts",
        overwrite_policy: OverwritePolicy = "always",
        **deprecated_bool: object,
    ) -> MetadataBuilder:
        """
        Deep-merge a mapping into the dict found at *path*.

        Nested dicts are merged recursively. Non-dict values follow the policy:
        - ``overwrite_policy="always"`` replaces existing values.
        - ``overwrite_policy="if_absent"`` only sets when the key is missing.

        ``create_policy`` controls whether a missing dict is created at the target.
        """
        if "create" in deprecated_bool:
            create_policy = "dicts" if bool(deprecated_bool["create"]) else "never"
        if "overwrite" in deprecated_bool:
            overwrite_policy = "always" if bool(deprecated_bool["overwrite"]) else "if_absent"

        create_flag = create_policy == "dicts"
        parent, key = _resolve_pointer(self._md, path, create=create_flag)
        if parent is None:
            msg = "Cannot merge into root; use set_path('/') if you truly need root replacement."
            raise ValueError(msg)

        target = _ensure_dict_target(parent, key, path, create_flag=create_flag)

        for k, v in mapping.items():
            _merge_into_target(
                self,
                target,
                path,
                k,
                v,
                create_policy=create_policy,
                overwrite_policy=overwrite_policy,
            )

        return self

    def merge_list(
        self,
        path: str,
        values: Iterable[object],
        *,
        strategy: ListStrategy = "concat",
        key: Optional[Callable[[object], object]] = None,
    ) -> MetadataBuilder:
        """
        Merge a list at *path* with the provided *values* using a strategy.

        Strategies
        ----------
        - ``"replace"``: replace existing list with ``values``.
        - ``"concat"``: append ``values`` to existing list (creating if absent).
        - ``"dedupe"``: concat then drop duplicates, using ``key(item)`` or ``repr(item)``.
        """
        parent, k = _resolve_pointer(self._md, path, create=True)
        base: object
        if isinstance(parent, list):
            idx = int(k)
            base = parent[idx]
        elif isinstance(parent, dict):
            base = parent.get(k)
        else:
            raise TypeError(f"List parent at '{path}' must be list or mapping.")

        if base is None or not isinstance(base, list) or strategy == "replace":
            new_list = list(values)
        elif strategy == "concat":
            new_list = list(base) + list(values)
        elif strategy == "dedupe":
            seen: set[object] = set()
            out: list[object] = []
            for item in list(base) + list(values):
                ident = key(item) if key else repr(item)
                if ident not in seen:
                    seen.add(ident)
                    out.append(item)
            new_list = out
        else:
            raise ValueError(f"Unknown strategy: {strategy!r}")

        if isinstance(parent, list):
            parent[int(k)] = new_list
        else:
            parent[k] = new_list
        return self

    def set_field_descriptions_for_index(
        self,
        index: int,
        descriptions: dict[str, str],
        *,
        default_nullable: bool | None = None,
    ) -> None:
        """Set schema field descriptions for a resource by index."""
        resources = self._md.get("resources", [])
        if not isinstance(resources, list):
            return
        if index < 0 or index >= len(resources):
            raise IndexError(f"Resource index {index} out of range.")

        res = resources[index]
        if not isinstance(res, dict):
            return

        schema = res.get("schema", {})
        if not isinstance(schema, dict):
            return

        fields = schema.get("fields", [])
        if not isinstance(fields, list):
            return

        for f in fields:
            if not isinstance(f, dict):
                continue
            fname = f.get("name")
            if isinstance(fname, str) and fname in descriptions:
                f["description"] = descriptions[fname]
            if default_nullable is not None and "nullable" not in f:
                f["nullable"] = default_nullable

    # ---------- High-level convenience (dataset-level) ----------

    def set_publication_date(self, date_iso: str) -> MetadataBuilder:
        """Set top-level ``publicationDate`` to an ISO-8601 string."""
        return self.set_path("/publicationDate", date_iso)

    def append_contributor_dataset(
        self,
        contributor: dict[str, object],
        *,
        dedupe_on: str = "title",
    ) -> MetadataBuilder:
        """Append a contributor to dataset-level ``/contributors`` (de-duplicated)."""

        def _ident(x: object) -> object:
            return x.get(dedupe_on) if isinstance(x, dict) else repr(x)

        return self.merge_list("/contributors", [contributor], strategy="dedupe", key=_ident)

    def append_contributor(
        self,
        _contributor: dict[str, object],
        *,
        _dedupe_on: str = "title",
    ) -> MetadataBuilder:
        """
        (Guarded) Append a contributor at the **dataset level**.

        This method now deliberately **raises** to prevent accidental placement of
        contributors on the dataset if you intended to target a resource.

        Use one of:
          - ``append_contributor_dataset(...)`` for dataset-level on purpose, or
          - ``.resource('name').append_contributor(...)`` for resource-level.
        """
        msg = (
            "append_contributor() at the root is ambiguous. Use "
            "append_contributor_dataset(...) for dataset-level or "
            "ResourceScope.append_contributor(...) within .resource(...)."
        )
        raise RuntimeError(
            msg,
        )

    def set_resource_field_descriptions(
        self,
        resource_name: str,
        descriptions: dict[str, str],
        *,
        default_nullable: Optional[bool] = None,
    ) -> MetadataBuilder:
        """
        Set descriptions (and optional default ``nullable``) for schema fields.

        Parameters
        ----------
        resource_name :
            Name of the target resource (its ``name`` property).
        descriptions :
            Mapping field-name → description string.
        default_nullable :
            If provided, set ``nullable`` when the key is missing (never overwrites).
        """
        resources = self._md.get("resources", [])
        if not isinstance(resources, list):
            return self

        for res in resources:
            if not isinstance(res, dict) or res.get("name") != resource_name:
                continue
            schema = res.get("schema", {})
            if not isinstance(schema, dict):
                continue
            fields = schema.get("fields", [])
            if not isinstance(fields, list):
                continue

            for f in fields:
                if not isinstance(f, dict):
                    continue
                fname = f.get("name")
                if isinstance(fname, str) and fname in descriptions:
                    f["description"] = descriptions[fname]
                if default_nullable is not None and "nullable" not in f:
                    f["nullable"] = default_nullable
        return self

    def add_keywords(self, keywords: list[str]) -> MetadataBuilder:
        """Add dataset-level keywords with de-duplication."""
        return self.merge_list("/keywords", keywords, strategy="dedupe")

    def ensure_template_defaults(self) -> MetadataBuilder:
        """(Reserved) Apply template-like defaults using the loaded spec, if any."""
        return self

    # ---------- Hygiene (schema-driven) ----------

    def ensure_required(self, *, oem_schema: dict) -> MetadataBuilder:
        """Ensure all required properties exist (with ``None``) according to the schema."""
        req = _collect_required_paths(oem_schema)
        self._md = _ensure_required_paths(self._md, req)
        return self

    def prune_empty(self, *, oem_schema: dict) -> MetadataBuilder:
        """Remove empty (None/''/[]/{}) properties unless required by the schema."""
        req = _collect_required_paths(oem_schema)
        self._md = _prune_empty(self._md, req)
        return self

    def lint(self) -> list[str]:
        """Run non-destructive lint checks against the current metadata snapshot."""
        return lint_metadata_against_schema(self._md)  # type: ignore[arg-type]

    def normalize(self, **opts) -> MetadataBuilder:
        """
        Normalize the in-memory metadata to better match the v2 schema.

        Options are forwarded to `normalize_metadata_for_schema(...)`.
        """
        self._md = normalize_metadata_for_schema(self._md, **opts)  # type: ignore[arg-type]
        return self

    def strip_unknown(self, *, oem_schema: dict) -> MetadataBuilder:
        """Strip keys not allowed by the given OEMetadata JSON Schema."""
        self._md = strip_unknown_keys(self._md, oem_schema=oem_schema)  # type: ignore[arg-type]
        return self

    def unknown_keys(self, *, oem_schema: dict) -> list[str]:
        """List JSON-Pointer paths to keys not allowed by the given schema."""
        return detect_unknown_keys(self._md, oem_schema=oem_schema)  # type: ignore[arg-type]

    # ---------- Finalize ----------

    def build(
        self,
        *,
        validate_policy: ValidatePolicy = "validate",
        license_policy: LicensePolicy = "skip",
        # backward-compat shims:
        **deprecated_bool: object,
    ) -> Json:
        """
        Return the final OEMetadata dict, optionally validated.

        Parameters
        ----------
        validate_policy :
            Run schema validation (``"validate"``) or skip (``"skip"``). Default ``"validate"``.
        license_policy :
            Check license compliance (``"check"``) or skip (``"skip"``). Default ``"skip"``.
        deprecated_bool :
            Backwards-compat shim for legacy boolean keyword arguments such as
            ``validate=...`` or ``check_license=...``. Prefer the explicit policy
            enums instead

        Returns
        -------
        dict[str, object]
            Deep-copied metadata dictionary (safe for caller mutation).
        """
        if "validate" in deprecated_bool:
            validate_policy = "validate" if bool(deprecated_bool["validate"]) else "skip"
        if "check_license" in deprecated_bool:
            license_policy = "check" if bool(deprecated_bool["check_license"]) else "skip"

        out = deepcopy(self._md)
        if validate_policy == "validate":
            validate_metadata(out, check_license=(license_policy == "check"))
        return out

    # ---------- Resource selection ----------

    def resource(self, selector: int | str) -> _ResourceScope:
        """
        Return a scoped helper for a specific resource.

        Parameters
        ----------
        selector :
            - ``int`` index in ``resources``; or
            - ``str`` resource.name (must be unique).
        """
        if isinstance(selector, int):
            idx = selector
        else:
            matches = [
                i
                for i, r in enumerate(self._md.get("resources", []))
                if isinstance(r, dict) and r.get("name") == selector
            ]
            if not matches:
                raise ValueError(f"Resource named '{selector}' not found.")
            if len(matches) > 1:
                raise ValueError(f"Multiple resources named '{selector}' found; select by index.")
            idx = matches[0]
        return _ResourceScope(self, idx)
