"""
Initialization helpers for OEMetadata split-files layout.

Provides functions to scaffold dataset and resource YAML files and to
infer resource information from existing data files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import yaml

from omi.base import get_metadata_specification
from omi.inspection import InspectionError, infer_metadata

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


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
    blank.setdefault("name", dataset_id)
    blank.setdefault("title", "")
    blank.setdefault("description", "")
    blank.setdefault("@id", "")

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


def init_resources_from_files(
    base_dir: Path,
    dataset_id: str,
    files: Iterable[Path],
    *,
    oem_version: str = "OEMetadata-2.0.4",
    overwrite: bool = False,
) -> list[Path]:
    """
    Create resource stubs for DATASET_ID from the given FILES.

    Uses the spec resource template structure, prefills name/path/format hints,
    and for CSV files also infers a schema (fields + types) using `omi.inspection`.
    """
    _ = get_metadata_specification(oem_version)

    outputs: list[Path] = []
    for f in files:
        name = f.stem
        ext = f.suffix.lower().lstrip(".")
        res = _resource_stub_from_spec(oem_version, name)
        res["path"] = str(f)

        # Lightweight format hinting (non-authoritative; user should review)
        if ext == "csv":
            res.setdefault("format", "CSV")
            res.setdefault("encoding", "UTF-8")
            res.setdefault("scheme", "file")

            # Use existing inspection: "OEP" == OEMetadata in this code base
            try:
                inferred = infer_metadata(str(f), metadata_format="OEP")
            except InspectionError:
                inferred = None

            if inferred is not None:
                # We only care about the *resource* part here
                try:
                    inferred_resource = inferred["resources"][0]
                    inferred_schema = inferred_resource.get("schema")
                except (KeyError, IndexError, TypeError):
                    inferred_schema = None

                if inferred_schema:
                    # Overwrite/attach the schema from inspection to this resource stub
                    res["schema"] = inferred_schema

        elif ext == "json":
            res.setdefault("format", "json")
            res.setdefault("scheme", "file")
        elif ext == "xlsx":
            res.setdefault("format", "xlsx")
            res.setdefault("scheme", "file")
        else:
            if ext:
                res.setdefault("format", ext)
            res.setdefault("scheme", "file")

        out_path = base_dir / "resources" / dataset_id / f"{name}.resource.yaml"
        outputs.append(_dump_yaml(out_path, res, overwrite=overwrite))

    return outputs
