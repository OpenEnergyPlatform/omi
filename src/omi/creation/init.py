"""
Initialization helpers for OEMetadata split-files layout.

Provides functions to scaffold dataset and resource YAML files and to
infer resource information from existing data files.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Union

import yaml

from omi.base import MetadataError, get_metadata_specification
from omi.creation.builder import MetadataBuilder
from omi.inspection import InspectionError, infer_metadata, inspect_db_table

from .utils import (
    collect_common_resource_fields,
    dump_yaml,
    load_yaml,
    normalize_bounding_box_in_resource,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class InitResult:
    """Paths to created or reused YAML files for a single dataset."""

    dataset_yaml: Path
    template_yaml: Path
    resource_yamls: list[Path]


# -----------------------------
# helpers
# -----------------------------


def _blankify(obj: object) -> object:
    """
    Return a copy of `obj` with the same structure but 'empty' leaf values.

    Rules:
    - dict  -> recursively blankify values
    - list  -> [] if scalar list; if list of dicts and non-empty, keep one blankified element; else []
    - str   -> ""
    - bool  -> False
    - int/float -> ""   (prefer empty so users must choose proper types)
    - None  -> None
    - everything else -> ""
    """
    if isinstance(obj, dict):
        blank: object = {k: _blankify(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if not obj:
            blank = []
        else:
            first = obj[0]
            # show one skeleton item so users see the structure for list-of-dicts;
            # scalar lists -> show empty by default
            blank = [_blankify(first)] if isinstance(first, dict) else []
    elif isinstance(obj, str):
        blank = ""
    elif isinstance(obj, bool):
        blank = False
    elif obj is None:
        blank = None
    else:
        # numbers / other scalars -> empty
        blank = ""
    return blank


def _is_empty(value: object) -> bool:
    """
    Return True if `value` counts as "not filled in yet".

    The blank skeletons produced by :func:`_blankify` contain every spec key
    with an empty value, so a plain ``dict.setdefault`` would never fire. This
    predicate is what makes "fill in a default unless the user provided
    something" work on those skeletons.
    """
    return value is None or value == "" or value == [] or value == {}


def _fill_if_empty(target: dict, key: str, value: object) -> None:
    """Set `target[key]` to `value` if the key is missing or still empty."""
    if _is_empty(target.get(key)):
        target[key] = value


def _load_spec_template(oem_version: str) -> dict:
    """Return the raw OEMetadata template document for the given version."""
    spec = get_metadata_specification(oem_version)
    return spec.template or {}


def _dataset_stub_from_spec_template(oem_version: str, dataset_id: str) -> dict:
    """
    Build datasets/<id>.dataset.yaml from top-level template (not from resources).

    Remove @context/resources/metaMetadata and blankify the rest.
    """
    t = _load_spec_template(oem_version).copy()
    t.pop("@context", None)
    t.pop("resources", None)  # <-- filter out resource-level keys
    t.pop("metaMetadata", None)

    blank = _blankify(t)
    _fill_if_empty(blank, "name", dataset_id)
    for key in ("title", "description", "@id"):
        blank.setdefault(key, "")

    return {"version": oem_version, "dataset": blank}


def _resource_template_from_spec(oem_version: str) -> dict:
    """Build datasets/<id>.template.yaml from the *first* resource template only."""
    tmpl = _load_spec_template(oem_version)
    resources = tmpl.get("resources") or []
    base = resources[0] if resources else {}
    return _blankify(base)


def _resource_stub_from_spec(oem_version: str, resource_name: str) -> dict:
    """Build resources/<id>/<name>.resource.yaml from the resource template."""
    res = _resource_template_from_spec(oem_version)
    res["name"] = resource_name
    return res


def _dump_yaml(path: Path, data: dict, *, overwrite: bool) -> Path:
    """Write `data` as YAML to `path`, respecting the `overwrite` flag."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return path
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Init from an existing OEMetadata JSON document
# ---------------------------------------------------------------------------

_RESOURCE_KEYS_FROM_OEM: tuple[str, ...] = (
    "@id",
    "name",
    "topics",
    "title",
    "path",
    "description",
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
    "scheme",  # used by tooling, not part of spec, but safe to keep
)


def _merge_known_resource_keys_from_oem(dst: dict, src: dict) -> dict:
    """
    Copy a subset of resource keys from an existing OEMetadata JSON resource.

    Also normalizes the boundingBox, so later JSON Schema validation won't
    fail on `['', '', '', '']`.
    """
    for k in _RESOURCE_KEYS_FROM_OEM:
        if k in src:
            dst[k] = src[k]
    normalize_bounding_box_in_resource(dst)
    return dst


def _update_dataset_yaml_from_top_level(dataset_yaml_path: Path, top: dict) -> None:
    """
    Enrich datasets/<id>.dataset.yaml with top-level OEMetadata information.

    Copies:
    - dataset.name / title / description / @id

    Does *not* copy metaMetadata, because that is owned by the spec and will
    be added by OEMetadataCreator later.
    """
    doc = load_yaml(dataset_yaml_path)
    ds = doc.get("dataset") or {}

    for key in ("name", "title", "description", "@id"):
        value = top.get(key)
        if value not in (None, ""):
            ds[key] = value

    doc["dataset"] = ds
    dump_yaml(dataset_yaml_path, doc)


def _apply_format_hints(res: dict, ext: str) -> None:
    """
    Fill in format/encoding/scheme hints for a resource based on its file extension.

    Only empty values are filled, so information the user already provided (or
    that was imported from elsewhere) is never overwritten.
    """
    if ext == "csv":
        _fill_if_empty(res, "type", "table")
        _fill_if_empty(res, "format", "CSV")
        _fill_if_empty(res, "encoding", "UTF-8")
    elif ext == "xlsx":
        _fill_if_empty(res, "type", "table")
        _fill_if_empty(res, "format", "xlsx")
    elif ext == "json":
        _fill_if_empty(res, "format", "json")
    elif ext:
        _fill_if_empty(res, "format", ext)
    _fill_if_empty(res, "scheme", "file")


def _apply_inferred_csv_schema(res: dict, file: Path, delimiter: str | None) -> None:
    """
    Attach schema and dialect inferred from a CSV file to a resource stub.

    Uses `omi.inspection`, which detects the column delimiter unless one is
    given explicitly. Inference failures are non-fatal: the stub simply keeps
    its blank schema.
    """
    # Use existing inspection: "OEP" == OEMetadata in this code base
    try:
        inferred = infer_metadata(str(file), metadata_format="OEP", delimiter=delimiter)
    except InspectionError:
        return

    # We only care about the *resource* part here
    try:
        inferred_resource = inferred["resources"][0]
    except (KeyError, IndexError, TypeError):
        return

    if inferred_resource.get("schema"):
        # Overwrite/attach the schema from inspection to this resource stub
        res["schema"] = inferred_resource["schema"]
    if inferred_resource.get("dialect"):
        # Carry the detected delimiter/decimalSeparator over
        res["dialect"] = inferred_resource["dialect"]


# -----------------------------
# public API
# -----------------------------


def init_dataset(
    base_dir: Path,
    dataset_id: str,
    *,
    oem_version: str = "OEMetadata-2.0",
    resources: Iterable[str] = (),
    overwrite: bool = False,
) -> InitResult:
    """
    Create or extend the split-files layout for one dataset.

    Creates:

    - datasets/<id>.dataset.yaml
    - datasets/<id>.template.yaml
    - resources/<id>/<resource>.resource.yaml for each requested resource.
    """
    # touch spec (also ensures the version string is valid)
    _ = get_metadata_specification(oem_version)

    dataset_yaml = base_dir / "datasets" / f"{dataset_id}.dataset.yaml"
    template_yaml = base_dir / "datasets" / f"{dataset_id}.template.yaml"

    dataset_doc = _dataset_stub_from_spec_template(oem_version, dataset_id)
    resource_template_doc = _resource_template_from_spec(oem_version)

    out_dataset = _dump_yaml(dataset_yaml, dataset_doc, overwrite=overwrite)
    out_template = _dump_yaml(template_yaml, resource_template_doc, overwrite=overwrite)

    created_resources: list[Path] = []
    for res_name in resources:
        res_doc = _resource_stub_from_spec(oem_version, res_name)
        res_path = base_dir / "resources" / dataset_id / f"{res_name}.resource.yaml"
        created_resources.append(_dump_yaml(res_path, res_doc, overwrite=overwrite))

    return InitResult(dataset_yaml=out_dataset, template_yaml=out_template, resource_yamls=created_resources)


def init_resources_from_files(  # noqa: PLR0913
    base_dir: Path,
    dataset_id: str,
    files: Iterable[Path],
    *,
    oem_version: str = "OEMetadata-2.0",
    overwrite: bool = False,
    delimiter: str | None = None,
) -> list[Path]:
    """
    Create resource stubs for DATASET_ID from the given FILES.

    Uses the spec resource template structure, prefills name/path/format hints,
    and for CSV files also infers a schema (fields + types) using `omi.inspection`.

    Parameters
    ----------
    base_dir :
        Base metadata directory (contains `datasets/` and `resources/`).
    dataset_id :
        Identifier of the dataset the resources belong to.
    files :
        Data files to create resource stubs for.
    oem_version :
        OEMetadata version string used for the spec/template.
    overwrite :
        Overwrite existing resource YAML files.
    delimiter :
        Column delimiter of the CSV files. If None (default), it is detected
        per file by `omi.inspection.detect_delimiter`.
    """
    _ = get_metadata_specification(oem_version)

    outputs: list[Path] = []
    for f in files:
        name = f.stem
        ext = f.suffix.lower().lstrip(".")
        res = _resource_stub_from_spec(oem_version, name)
        res["path"] = str(f)

        # Lightweight format hinting (non-authoritative; user should review)
        _apply_format_hints(res, ext)
        if ext == "csv":
            _apply_inferred_csv_schema(res, f, delimiter)

        out_path = base_dir / "resources" / dataset_id / f"{name}.resource.yaml"
        outputs.append(_dump_yaml(out_path, res, overwrite=overwrite))

    return outputs


def init_from_oem_json(
    base_dir: Path,
    dataset_id: str,
    oem_json_path: Path,
    *,
    oem_version: str = "OEMetadata-2.0",
    collect_common: bool = False,
) -> InitResult:
    """
    Initialise split-YAML layout (dataset + template + resources) from an.

    existing OEMetadata JSON document that may contain multiple resources.

    Parameters
    ----------
    base_dir :
        Base metadata directory (contains `datasets/` and `resources/`).
    dataset_id :
        Identifier for `<id>.dataset.yaml`, `<id>.template.yaml` and the
        `resources/<id>/` folder.
    oem_json_path :
        Path to the OEMetadata JSON file to import.
    oem_version :
        OEMetadata version string used for the spec/template.
    collect_common :
        If True, fields that are common across resources (context/spatial/
        temporal/sources/licenses/contributors) are hoisted into the template.

    Returns
    -------
    InitResult
        Paths to the dataset YAML, template YAML and created resource YAMLs.
    """
    base_dir = Path(base_dir)
    oem = json.loads(Path(oem_json_path).read_text(encoding="utf-8"))

    # 1) Create dataset + template stubs (from spec template)
    init_result = init_dataset(
        base_dir=base_dir,
        dataset_id=dataset_id,
        oem_version=oem_version,
        resources=(),
        overwrite=False,
    )

    # 2) Enrich dataset YAML from top-level OEMetadata info
    _update_dataset_yaml_from_top_level(init_result.dataset_yaml, oem)
    # metaMetadata stays handled centrally by OEMetadataCreator

    # 3) Create resource YAMLs from OEMetadata resources
    resources = oem.get("resources", [])
    res_dir = base_dir / "resources" / dataset_id
    res_dir.mkdir(parents=True, exist_ok=True)

    created_resources: list[Path] = []
    for res in resources:
        if not isinstance(res, dict):
            continue

        raw_name = (res.get("name") or "").strip()
        name = raw_name or Path(str(res.get("path", "resource"))).stem

        out: dict[str, object] = {"name": name}
        out = _merge_known_resource_keys_from_oem(out, res)

        out_path = res_dir / f"{name}.resource.yaml"
        created_resources.append(dump_yaml(out_path, out))

    # 4) Optionally collect common fields for template (e.g. context/spatial/temporal/...)
    if collect_common:
        collect_common_resource_fields(base_dir, dataset_id)

    return InitResult(
        dataset_yaml=init_result.dataset_yaml,
        template_yaml=init_result.template_yaml,
        resource_yamls=created_resources,
    )


def add_resource_from_oem_metadata(  # noqa: PLR0913
    base_dir: Union[str, Path],
    dataset_id: str,
    oem: dict,
    *,
    resource_index: int = 0,
    resource_name: str | None = None,
    overwrite: bool = False,
    oem_version: str = "OEMetadata-2.0",
    fill_missing_from_template: bool = False,
) -> Path:
    """
    Add a single resource YAML file to an existing dataset from an OEMetadata json.

    Notes
    -----
    - The given OEMetadata object may be a complete OEP meta JSON document.
      The top-level dataset fields (id, name, title, @id, @context, description, ...)
      are ignored.
    - Only the entry at ``oem["resources"][resource_index]`` is converted into
      a ``.resource.yaml`` file.
    - If ``fill_missing_from_template=True``, the resource is first initialized
      from the OEMetadata spec resource template (all keys present with empty
      values) and then overlaid with the OEP values. This makes it easier to
      see which fields are still missing when editing the YAML.

    Parameters
    ----------
    base_dir :
        Base directory containing ``datasets/`` and ``resources/``.
    dataset_id :
        ID of the local dataset (corresponds to ``resources/<dataset_id>/``).
    oem :
        OEMetadata mapping, e.g. directly from the OEP API.
    resource_index :
        Index within ``oem["resources"]``, default is 0.
    resource_name :
        Optional explicit resource name. If None, the name is taken from the
        OEMetadata resource or derived from its ``path``.
    overwrite :
        If False (default) and the ``.resource.yaml`` already exists, a
        ``FileExistsError`` is raised.
    oem_version :
        OEMetadata version string (e.g. ``"OEMetadata-2.0"``) used to select
        the appropriate resource template when ``fill_missing_from_template``
        is True.
    fill_missing_from_template :
        If True, start from the blank resource template from the spec and
        merge the OEP resource into it, so all known fields are visible
        (with empty values where not provided).

    Returns
    -------
    Path
        Path to the created or overwritten resource YAML file.
    """
    base_dir = Path(base_dir)
    resources = oem.get("resources") or []
    if not resources:
        msg = "OEMetadata document contains no resources."
        raise MetadataError(msg)

    if resource_index < 0 or resource_index >= len(resources):
        raise IndexError(
            f"Resource index {resource_index} out of range for OEMetadata.resources (len={len(resources)}).",
        )

    res = resources[resource_index]
    if not isinstance(res, dict):
        msg = "OEMetadata resource entry is not a mapping."
        raise MetadataError(msg)

    raw_name = resource_name or (res.get("name") or "").strip()
    if not raw_name:
        raw_name = Path(str(res.get("path", "resource"))).stem

    # Start either from a full blank resource template (all keys) or from a minimal dict
    base = _resource_stub_from_spec(oem_version, raw_name) if fill_missing_from_template else {"name": raw_name}

    # Overlay OEP info onto that base
    out: dict[str, object] = _merge_known_resource_keys_from_oem(base, res)

    res_dir = base_dir / "resources" / dataset_id
    res_dir.mkdir(parents=True, exist_ok=True)
    out_path = res_dir / f"{raw_name}.resource.yaml"

    if out_path.exists() and not overwrite:
        raise FileExistsError(f"Resource YAML already exists: {out_path}")

    dump_yaml(out_path, out)
    return out_path


# ---------------------------------------------------------------------------
# Non-destructive merge-update of a resource from a DB-inspection skeleton
# ---------------------------------------------------------------------------


def update_resource_from_db_skeleton(
    resource: dict,
    db_skeleton: dict,
    *,
    strict: bool = False,
) -> tuple[dict, dict]:
    """
    Merge a DB-inspection skeleton into an existing resource, non-destructively.

    Human-authored content in ``resource`` (field descriptions, units, titles)
    is preserved; the database supplies structural truth (column presence,
    types, nullability). Columns present in the DB but absent from the YAML are
    added with a ``TODO`` description placeholder; columns present in the YAML
    but absent from the DB are kept and reported as drift.

    Parameters
    ----------
    resource :
        An OEMetadata resource dict (as loaded from a ``.resource.yaml``).
    db_skeleton :
        The resource skeleton produced by :func:`omi.inspection.inspect_db_table`.
    strict :
        If True, raise ``SchemaDriftError`` when columns are missing on either
        side instead of merging and reporting.

    Returns
    -------
    (updated_resource, drift_report)
        ``updated_resource`` is a new dict (the input is not mutated);
        ``drift_report`` has keys ``missing_in_yaml``, ``missing_in_db`` and
        ``type_mismatches``.
    """
    builder = MetadataBuilder({"resources": [deepcopy(resource)]})
    report = builder.resource(0).merge_and_diff_db_schema(db_skeleton, strict=strict)
    updated = builder.build(validate_policy="skip")["resources"][0]
    return dict(updated), report


def update_resource_yaml_from_db(  # noqa: PLR0913
    base_dir: Union[str, Path],
    dataset_id: str,
    resource_name: str,
    engine_or_url: object,
    *,
    schema_name: str | None = None,
    table_name: str | None = None,
    strict: bool = False,
) -> tuple[Path, dict]:
    """
    Update a resource YAML in place from a live database table.

    Loads ``resources/<dataset_id>/<safe_name>.resource.yaml`` (where
    ``safe_name`` is ``resource_name`` with ``.`` replaced by ``_``), inspects
    the corresponding DB table, merges the schema non-destructively via
    :func:`update_resource_from_db_skeleton`, and writes the file back.

    ``schema_name`` / ``table_name`` default to the two halves of a dotted
    ``resource_name`` (``schema.table``).

    Returns
    -------
    (resource_path, drift_report)
    """
    base_dir = Path(base_dir)
    safe_name = resource_name.replace(".", "_")
    resource_path = base_dir / "resources" / dataset_id / f"{safe_name}.resource.yaml"
    if not resource_path.exists():
        raise FileNotFoundError(f"Resource YAML not found: {resource_path}")

    if schema_name is None or table_name is None:
        parts = resource_name.split(".")
        expected_parts = 2
        if len(parts) == expected_parts:
            schema_name = schema_name or parts[0]
            table_name = table_name or parts[1]
        else:
            table_name = table_name or resource_name

    db_skeleton = inspect_db_table(engine_or_url, schema_name or "", table_name or "")

    resource = load_yaml(resource_path)
    updated, report = update_resource_from_db_skeleton(resource, db_skeleton, strict=strict)
    dump_yaml(resource_path, updated)
    return resource_path, report
