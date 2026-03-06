# omi/creation/merge.py
"""Merge functionality for OEMetadata objects."""
from __future__ import annotations

from copy import deepcopy

Json = dict[str, object]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

_EMPTY = (None, "", [], {})


def _is_empty(value: object) -> bool:
    return value in _EMPTY


def _merge_scalar(base: object, incoming: object, *, prefer: str = "incoming") -> object:
    """
    Merge two scalar-ish values (or treat lists/dicts as atomic).

    prefer="incoming":
      - if incoming is non-empty -> incoming
      - else                     -> base

    prefer="base" is the inverse.
    """
    if prefer not in ("incoming", "base"):
        msg = "prefer must be 'incoming' or 'base'."
        raise ValueError(msg)

    if prefer == "incoming":
        return incoming if not _is_empty(incoming) else base
    return base if not _is_empty(base) else incoming


def _union_list_scalars(a: object, b: object) -> list[object]:
    """Union of two scalar lists with de-duplication, preserving order."""
    # Filter for valid lists
    sources = [src for src in (a, b) if isinstance(src, list)]
    # Use dict keys for order-preserving deduplication
    return list({item: None for src in sources for item in src}.keys())


def _union_list_objects(a: object, b: object, key_fields: tuple[str, ...]) -> list[dict[str, object]]:
    """Union of two lists of dicts, de-duplicated by key_fields."""
    out: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()

    def sig(obj: object) -> tuple[object, ...]:
        if not isinstance(obj, dict):
            return (repr(obj),)
        return tuple(obj.get(k) for k in key_fields) or (repr(obj),)

    for src in (a or [], b or []):
        if not isinstance(src, list):
            continue
        for obj in src:
            if not isinstance(obj, dict):
                continue
            s = sig(obj)
            if s in seen:
                continue
            seen.add(s)
            out.append(deepcopy(obj))
    return out


# ---------------------------------------------------------------------------
# Schema / field merging
# ---------------------------------------------------------------------------


def _merge_field(
    base: dict[str, object],
    incoming: dict[str, object],
    *,
    prefer: str,
    warnings: list[str],
) -> dict[str, object]:
    """Merge two field dicts (same field name)."""
    result = deepcopy(base)

    name = base.get("name") or incoming.get("name")

    # Type changes are potentially breaking - warn but still resolve by prefer
    base_type = base.get("type")
    inc_type = incoming.get("type")
    if not _is_empty(base_type) and not _is_empty(inc_type) and base_type != inc_type:
        warnings.append(f"Field '{name}': type changed from {base_type!r} to {inc_type!r}; using {prefer} value.")

    # Simple scalar keys
    for key in ("type", "description", "unit", "nullable"):
        result[key] = _merge_scalar(base.get(key), incoming.get(key), prefer=prefer)

    # Arrays of small objects
    result["isAbout"] = _union_list_objects(
        base.get("isAbout"),
        incoming.get("isAbout"),
        key_fields=("name", "@id"),
    )
    result["valueReference"] = _union_list_objects(
        base.get("valueReference"),
        incoming.get("valueReference"),
        key_fields=("value", "name", "@id"),
    )

    # Extra keys from incoming (if non-empty)
    handled = {"name", "type", "description", "unit", "nullable", "isAbout", "valueReference"}
    for k, v in incoming.items():
        if k in handled:
            continue
        if _is_empty(v):
            continue
        result[k] = deepcopy(v)

    # Ensure name exists
    if "name" not in result:
        result["name"] = name

    return result


def _merge_schema_fields(
    base_fields: list[object],
    inc_fields: list[object],
    prefer: str,
    warnings: list[str],
) -> list[dict[str, object]]:
    """Merge the 'fields' list of a schema."""

    def by_name(fields: list[object]) -> dict[str, dict[str, object]]:
        out: dict[str, dict[str, object]] = {}
        for f in fields:
            if not isinstance(f, dict):
                continue
            name = f.get("name")
            if isinstance(name, str) and name:
                out[name] = f
        return out

    base_by_name = by_name(base_fields)
    inc_by_name = by_name(inc_fields)

    merged_fields: list[dict[str, object]] = []

    # keep base order; merge where incoming has same field
    for f in base_fields:
        if not isinstance(f, dict):
            continue
        name = f.get("name")
        if isinstance(name, str) and name in inc_by_name:
            merged_fields.append(_merge_field(f, inc_by_name[name], prefer=prefer, warnings=warnings))
        else:
            merged_fields.append(deepcopy(f))

    # add new fields from incoming that were not in base
    for name, f in inc_by_name.items():
        if name not in base_by_name:
            merged_fields.append(deepcopy(f))

    return merged_fields


def _merge_schema(
    base: object,
    incoming: object,
    *,
    prefer: str,
    warnings: list[str],
) -> dict[str, object]:
    """Merge the 'schema' dict of a resource."""
    if not isinstance(base, dict) and not isinstance(incoming, dict):
        return {}

    base_schema = base if isinstance(base, dict) else {}
    inc_schema = incoming if isinstance(incoming, dict) else {}

    result: dict[str, object] = deepcopy(base_schema)

    # --- fields ---
    base_fields = base_schema.get("fields") or []
    inc_fields = inc_schema.get("fields") or []

    if not isinstance(base_fields, list):
        base_fields = []
    if not isinstance(inc_fields, list):
        inc_fields = []

    merged_fields = _merge_schema_fields(base_fields, inc_fields, prefer, warnings)

    if merged_fields:
        result["fields"] = merged_fields

    # --- primaryKey ---
    pk = _merge_scalar(base_schema.get("primaryKey"), inc_schema.get("primaryKey"), prefer=prefer)
    if pk is not None:
        result["primaryKey"] = pk

    # --- foreignKeys ---
    fk = _merge_scalar(base_schema.get("foreignKeys"), inc_schema.get("foreignKeys"), prefer=prefer)
    if fk is not None and fk != {}:
        result["foreignKeys"] = fk

    # Extra schema keys from incoming, if non-empty
    handled = {"fields", "primaryKey", "foreignKeys"}
    for k, v in inc_schema.items():
        if k in handled:
            continue
        if _is_empty(v):
            continue
        result[k] = deepcopy(v)

    return result


# ---------------------------------------------------------------------------
# Resource and dataset-level merging
# ---------------------------------------------------------------------------


def _merge_resource(
    base: dict[str, object],
    incoming: dict[str, object],
    *,
    prefer: str,
    warnings: list[str],
) -> dict[str, object]:
    """Merge two resource dicts with the same resource name."""
    result = deepcopy(base)

    # Simple scalar keys at resource level
    scalar_keys = [
        "title",
        "description",
        "path",
        "@id",
        "publicationDate",
        "type",
        "format",
        "encoding",
    ]
    for key in scalar_keys:
        result[key] = _merge_scalar(base.get(key), incoming.get(key), prefer=prefer)

    # Arrays of scalars
    for key in ("keywords", "topics", "languages"):
        result[key] = _union_list_scalars(base.get(key), incoming.get(key))

    # Object arrays
    result["contributors"] = _union_list_objects(
        base.get("contributors"),
        incoming.get("contributors"),
        key_fields=("title", "organization", "path"),
    )
    result["sources"] = _union_list_objects(
        base.get("sources"),
        incoming.get("sources"),
        key_fields=("title", "publicationYear", "path"),
    )
    result["licenses"] = _union_list_objects(
        base.get("licenses"),
        incoming.get("licenses"),
        key_fields=("name", "path"),
    )

    # Simple dict blocks: context, spatial, temporal, embargoPeriod, dialect, review
    for key in ("context", "spatial", "temporal", "embargoPeriod", "dialect", "review"):
        b_val = base.get(key)
        i_val = incoming.get(key)
        if isinstance(b_val, dict) or isinstance(i_val, dict):
            merged_block: dict[str, object] = {}
            b_dict = b_val if isinstance(b_val, dict) else {}
            i_dict = i_val if isinstance(i_val, dict) else {}
            all_keys = set(b_dict) | set(i_dict)
            for sub_k in all_keys:
                merged_block[sub_k] = _merge_scalar(
                    b_dict.get(sub_k),
                    i_dict.get(sub_k),
                    prefer=prefer,
                )
            result[key] = merged_block

    # Schema
    result["schema"] = _merge_schema(
        base.get("schema"),
        incoming.get("schema"),
        prefer=prefer,
        warnings=warnings,
    )

    # Extra keys from incoming resource
    handled_keys = {
        "name",
        "@id",
        "title",
        "description",
        "path",
        "topics",
        "languages",
        "subject",
        "keywords",
        "publicationDate",
        "embargoPeriod",
        "context",
        "spatial",
        "temporal",
        "sources",
        "licenses",
        "contributors",
        "type",
        "format",
        "encoding",
        "schema",
        "dialect",
        "review",
    }
    for k, v in incoming.items():
        if k in handled_keys:
            continue
        if _is_empty(v):
            continue
        result[k] = deepcopy(v)

    return result


def _index_resources_by_name(resources: object) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    if not isinstance(resources, list):
        return out
    for res in resources:
        if not isinstance(res, dict):
            continue
        name = res.get("name")
        if isinstance(name, str) and name:
            out[name] = res
    return out


def _merge_resources_list(
    base_res: list[object],
    inc_res: list[object],
    prefer: str,
    warnings: list[str],
) -> list[dict[str, object]]:
    """Merge lists of resource dictionaries."""
    base_by_name = _index_resources_by_name(base_res)
    inc_by_name = _index_resources_by_name(inc_res)

    names_all = list(dict.fromkeys(list(base_by_name.keys()) + list(inc_by_name.keys())))
    merged_resources: list[dict[str, object]] = []

    for name in names_all:
        if name in base_by_name and name in inc_by_name:
            merged_resources.append(
                _merge_resource(base_by_name[name], inc_by_name[name], prefer=prefer, warnings=warnings),
            )
        elif name in base_by_name and name not in inc_by_name:
            warnings.append(f"Resource '{name}' present only in base metadata; keeping base version.")
            merged_resources.append(deepcopy(base_by_name[name]))
        elif name in inc_by_name and name not in base_by_name:
            warnings.append(f"Resource '{name}' present only in incoming metadata; adding as new resource.")
            merged_resources.append(deepcopy(inc_by_name[name]))

    return merged_resources


def _collect_unnamed_resources(resources: object) -> list[dict[str, object]]:
    """Collect resources that have no name."""
    out: list[dict[str, object]] = []
    if not isinstance(resources, list):
        return out
    for res in resources:
        if not isinstance(res, dict):
            continue
        name = res.get("name")
        if not isinstance(name, str) or not name:
            out.append(deepcopy(res))
    return out


def _merge_meta_metadata(
    base_meta: object,
    inc_meta: object,
    prefer: str,
) -> dict[str, object]:
    """Merge the metaMetadata dictionaries."""
    # Ensure they are dicts
    b_meta = base_meta if isinstance(base_meta, dict) else {}
    i_meta = inc_meta if isinstance(inc_meta, dict) else {}

    if not b_meta and not i_meta:
        return {}

    merged_meta: dict[str, object] = deepcopy(b_meta)
    for k, v in i_meta.items():
        merged_meta[k] = _merge_scalar(b_meta.get(k), v, prefer=prefer)
    return merged_meta


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_oemetadata(
    base: Json,
    incoming: Json,
    *,
    prefer: str = "incoming",
) -> tuple[Json, list[str]]:
    """
    Merge two OEMetadata dicts describing the *same dataset*.

    Preconditions
    -------------
    - Either 'name' or '@id' must match (if both present, at least one equal).

    Parameters
    ----------
    base :
        Original metadata (e.g. existing in DB).
    incoming :
        Newer metadata (e.g. updated YAML + builder).
    prefer :
        Conflict resolution when both sides have non-empty differing values:
        - 'incoming': prefer the incoming value (default).
        - 'base'    : keep the existing/base value.

    Returns
    -------
    (merged, warnings)
        merged  : merged OEMetadata dict
        warnings: list of human-readable warning strings
    """
    warnings: list[str] = []

    # --- preconditions: dataset identity ---
    base_name = base.get("name")
    inc_name = incoming.get("name")
    base_id = base.get("@id")
    inc_id = incoming.get("@id")

    same_name = base_name and inc_name and base_name == inc_name
    same_id = base_id and inc_id and base_id == inc_id

    if not (same_name or same_id):
        raise ValueError(
            f"Cannot merge metadata: dataset name/@id differ "
            f"(base name={base_name!r}, incoming name={inc_name!r}, "
            f"base @id={base_id!r}, incoming @id={inc_id!r}).",
        )

    merged: Json = deepcopy(base)

    # --- top-level scalars ---
    for key in ("title", "description", "name", "@id"):
        merged[key] = _merge_scalar(base.get(key), incoming.get(key), prefer=prefer)

    # --- metaMetadata ---
    merged_meta = _merge_meta_metadata(
        base.get("metaMetadata"),
        incoming.get("metaMetadata"),
        prefer,
    )
    if merged_meta:
        merged["metaMetadata"] = merged_meta

    # --- resources ---
    base_res = base.get("resources") or []
    inc_res = incoming.get("resources") or []

    # Cast to lists for the helper
    if not isinstance(base_res, list):
        base_res = []
    if not isinstance(inc_res, list):
        inc_res = []

    merged_resources = _merge_resources_list(base_res, inc_res, prefer, warnings)

    # Resources without a name: keep them from both, unchanged
    unnamed_base = _collect_unnamed_resources(base_res)
    unnamed_inc = _collect_unnamed_resources(inc_res)
    if unnamed_base:
        warnings.append(f"{len(unnamed_base)} unnamed resources from base kept unchanged.")
    if unnamed_inc:
        warnings.append(f"{len(unnamed_inc)} unnamed resources from incoming kept unchanged.")
    merged_resources.extend(unnamed_base)
    merged_resources.extend(unnamed_inc)

    merged["resources"] = merged_resources

    return merged, warnings
