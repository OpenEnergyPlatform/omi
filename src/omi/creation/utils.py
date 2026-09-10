"""
Utility functions for the OMI creation module.

This module provides deep-merge templating, YAML IO, and discovery helpers
for assembling OEMetadata from split YAML files (dataset/template/resources).
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

import yaml

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterable

# --- deep merge helpers -------------------------------------------------------

# List keys we concatenate (resource + template) instead of replacing.
DEFAULT_CONCAT_LIST_KEYS = {"keywords", "topics", "languages"}
OEM_BBOX_MIN_LENGTH = 4

# Used when a dataset YAML does not declare a `version`. Must be a version
# known to `omi.base.METADATA_FORMATS`, otherwise assembly fails.
DEFAULT_OEM_VERSION = "OEMetadata-2.0"


def _is_effectively_empty(value: object) -> bool:
    """
    Return True if `value` is 'empty' in the sense of 'no opinion'.

    - None or ""  -> empty
    - list/tuple/set -> empty if all elements are empty
    - dict -> empty if all values are empty
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0 or all(_is_effectively_empty(v) for v in value)
    if isinstance(value, dict):
        return len(value) == 0 or all(_is_effectively_empty(v) for v in value.values())
    return False


def _hashable_key(x: object) -> Hashable | tuple:
    """
    Return a hashable representation of `x` for deduplication purposes.

    - dict  -> sorted tuple of (key, value) pairs
    - list  -> tuple(list)
    - other -> value itself
    """
    if isinstance(x, dict):
        return tuple(sorted(x.items()))
    if isinstance(x, list):
        return tuple(x)
    return x  # type: ignore[return-value]


def _merge_lists(
    template_list: list[object],
    resource_list: list[object],
    *,
    deduplicate: bool = True,
) -> list[object]:
    """
    Concatenate lists with resource-first priority.

    When `deduplicate` is True, only items that are not already present in
    `resource_list` (by hashable representation) are appended from `template_list`.
    """
    merged = list(resource_list)
    if not template_list:
        return merged

    if deduplicate:
        existing = {_hashable_key(v) for v in merged}
        for item in template_list:
            k = _hashable_key(item)
            if k not in existing:
                merged.append(item)
    else:
        merged.extend(template_list)
    return merged


def deep_apply_template_to_resource(
    resource: dict[str, object],
    template: dict[str, object],
    concat_list_keys: Union[tuple[str, ...], set[str]] = DEFAULT_CONCAT_LIST_KEYS,
) -> dict[str, object]:
    """
    Apply a resource template using deep-merge semantics.

    Rules:
    - Missing keys are copied from the template.
    - **Effectively empty keys in resource are overwritten by template.**
      (e.g., `[{'title': ''}]` is considered empty and replaced by template).
    - Dicts are deep-merged (resource wins on conflicts).
    - Lists are concatenated only for keys in `concat_list_keys`; otherwise, the
      resource list is preserved as-is (unless it was effectively empty).
    - Scalars: resource values win.
    """
    if not template:
        return resource

    result = deepcopy(resource)
    for key, tval in template.items():
        if key not in result:
            result[key] = deepcopy(tval)
            continue

        rval = result[key]

        # This allows template to overwrite "scaffolding" (lists of empty dicts).
        if _is_effectively_empty(rval) and not _is_effectively_empty(tval):
            result[key] = deepcopy(tval)
            continue

        if isinstance(rval, dict) and isinstance(tval, dict):
            result[key] = deep_apply_template_to_resource(rval, tval, concat_list_keys)
            continue

        if isinstance(rval, list) and isinstance(tval, list):
            if key in concat_list_keys:
                result[key] = _merge_lists(tval, rval, deduplicate=True)
            # else: resource list stays as-is (because it's not effectively empty)
            continue
        # scalar: resource value stays
    return result


def apply_template_to_resources(
    resources: list[dict[str, object]],
    template: dict[str, object],
    *,
    concat_list_keys: Union[tuple[str, ...], set[str]] = DEFAULT_CONCAT_LIST_KEYS,
) -> list[dict[str, object]]:
    """Apply the same `template` to each resource in `resources`."""
    if not template:
        return resources
    return [deep_apply_template_to_resource(r, template, concat_list_keys=concat_list_keys) for r in resources]


# --- YAML IO + discovery ------------------------------------------------------


def load_yaml(path: Union[str, Path]) -> dict[str, object]:
    """Load a YAML mapping from `path`, returning an empty dict for empty files."""
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def discover_paths(
    base_dir: Union[str, Path],
    dataset_id: str,
) -> tuple[Optional[Path], Optional[Path], list[Path]]:
    """
    Discover dataset/template/resources paths by convention.

    - dataset:   datasets/{dataset_id}.dataset.yaml
    - template:  datasets/{dataset_id}.template.yaml  (optional)
    - resources: resources/{dataset_id}/*.resource.yaml
    """
    base = Path(base_dir)
    dataset_path = base / "datasets" / f"{dataset_id}.dataset.yaml"
    template_path = base / "datasets" / f"{dataset_id}.template.yaml"
    resources_dir = base / "resources" / dataset_id

    dataset = dataset_path if dataset_path.exists() else None
    template = template_path if template_path.exists() else None
    resources = sorted(resources_dir.glob("*.resource.yaml")) if resources_dir.exists() else []
    return dataset, template, resources


def resolve_from_index(
    base_dir: Union[str, Path],
    dataset_id: str,
    index_file: Optional[Union[str, Path]],
) -> tuple[Optional[Path], Optional[Path], list[Path]]:
    """
    Resolve dataset/template/resources using an explicit index YAML.

    Example YAML:

        datasets:
          <dataset_id>:
            dataset: path/to/dataset.yaml
            template: path/to/template.yaml   # optional
            resources:
              - path/to/res1.yaml
              - path/to/res2.yaml

    Paths are interpreted as relative to `base_dir`.

    Parameters
    ----------
    base_dir : Union[str, Path]
        Base directory containing datasets, templates, and resources.
    dataset_id : str
        Identifier for the dataset to load.
    index_file : Optional[Union[str, Path]]
        Optional path to an index YAML file for resolving dataset parts.

    Returns
    -------
    tuple[Optional[Path], Optional[Path], list[Path]]
        A tuple containing:
        - dataset_path: Optional[Path]
            Path to the dataset YAML (or None if not found).
        - template_path: Optional[Path]
            Path to the template YAML (or None if not found).
        - resource_paths: list[Path]
            List of paths to resource YAMLs.
    """
    if not index_file:
        return discover_paths(base_dir, dataset_id)

    base = Path(base_dir)
    index_path = Path(index_file)
    index = load_yaml(index_path)
    entry = (index.get("datasets") or {}).get(dataset_id, {})
    dataset = base / entry["dataset"] if "dataset" in entry else None
    template = base / entry["template"] if "template" in entry else None
    resources = [base / p for p in entry.get("resources", [])]
    return dataset, template, resources


def load_parts(
    base_dir: Union[str, Path],
    dataset_id: str,
    index_file: Optional[Union[str, Path]] = None,
) -> tuple[str, dict[str, object], list[dict[str, object]], dict[str, object]]:
    """
    Load dataset YAML, optional template YAML, and all resource YAMLs.

    Returns a tuple: (version, dataset, resources, template).

    Parameters
    ----------
    base_dir : Union[str, Path]
        Base directory containing datasets, templates, and resources.
    dataset_id : str
        Identifier for the dataset to load.
    index_file : Optional[Union[str, Path]], optional
        Optional path to an index YAML file for resolving dataset parts,
        by default None.

    Returns
    -------
    tuple[str, dict[str, object], list[dict[str, object]], dict[str, object]]
        A tuple containing:
        - version: str
            The OEMetadata version from the dataset YAML (default "OEMetadata-2.0").
        - dataset: dict[str, object]
            The dataset mapping from the dataset YAML.
        - resources: list[dict[str, object]]
            A list of resource mappings from the resource YAMLs.
        - template: dict[str, object]
            The template mapping from the template YAML (empty dict if none).
    """
    dataset_path, template_path, resource_paths = resolve_from_index(base_dir, dataset_id, index_file)

    if dataset_path is None or not dataset_path.exists():
        raise FileNotFoundError(f"Dataset YAML not found for '{dataset_id}'")

    dataset_yaml = load_yaml(dataset_path)
    version = str(dataset_yaml.get("version") or DEFAULT_OEM_VERSION)
    # Support either dataset: {...} or flat style with top-level dataset keys.
    dataset = dataset_yaml.get("dataset", dataset_yaml)

    template: dict[str, object] = {}
    if template_path and template_path.exists():
        template = load_yaml(template_path)

    resources: list[dict[str, object]] = [load_yaml(p) for p in resource_paths]
    return version, dataset, resources, template


def discover_dataset_ids(base_dir: Union[str, Path]) -> list[str]:
    """
    Discover dataset ids by scanning datasets/*.dataset.yaml.

    For 'datasets/powerplants.dataset.yaml' returns 'powerplants'.

    Parameters
    ----------
    base_dir : Union[str, Path]
        Base directory containing datasets, templates, and resources.

    Returns
    -------
    list[str]
        Sorted list of discovered dataset IDs.
    """
    base = Path(base_dir)
    datasets_dir = base / "datasets"
    if not datasets_dir.exists():
        return []
    return sorted([p.stem.replace(".dataset", "") for p in datasets_dir.glob("*.dataset.yaml")])


def discover_dataset_ids_from_index(index_file: Union[str, Path]) -> list[str]:
    """
    Discover dataset ids from an explicit metadata_index.yaml.

    Returns the sorted list of top-level keys under `datasets`.

    Parameters
    ----------
    index_file : Union[str, Path]
        Path to an index YAML file for resolving dataset parts.

    Returns
    -------
    list[str]
        Sorted list of discovered dataset IDs.
    """
    idx_path = Path(index_file)
    if not idx_path.exists():
        return []
    with idx_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    ds = data.get("datasets") or {}
    return sorted(ds.keys())


def dump_yaml(path: Union[str, Path], data: dict[str, object]) -> Path:
    """
    Write `data` as YAML to `path`, creating parent directories if needed.

    Returns
    -------
    Path
        The path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def normalize_bounding_box_in_resource(resource: dict[str, object]) -> None:
    """
    Ensure spatial.extent.boundingBox is JSON-schema friendly.

    Rules
    -----
    - If boundingBox is a list of 4 empty-ish values -> [0, 0, 0, 0].
    - If boundingBox is 4 numbers -> keep as-is.
    - Otherwise -> remove boundingBox (user can re-add a proper one).
    """
    spatial = resource.get("spatial")
    if not isinstance(spatial, dict):
        return

    extent = spatial.get("extent")
    if not isinstance(extent, dict):
        return

    bbox = extent.get("boundingBox")
    if bbox is None:
        return

    if not isinstance(bbox, list) or len(bbox) != OEM_BBOX_MIN_LENGTH:
        extent.pop("boundingBox", None)
        return

    # all empty-ish values → default to zeros
    if all(v in ("", None, "", 0, 0.0, False) for v in bbox):
        extent["boundingBox"] = [0, 0, 0, 0]
        return

    # mixed types → require all numbers, else drop
    if not all(isinstance(v, (int, float)) for v in bbox):
        extent.pop("boundingBox", None)


def _find_common_value_for_key(
    docs: list[dict[str, object]],
    key: str,
    min_resources: int,
) -> tuple[object, list[int]] | None:
    """
    For a given key, find the most common non-empty value across docs.

    Returns (value, indices) or None if there is no sufficiently common value.
    """
    clusters: list[tuple[object, list[int]]] = []

    for idx, d in enumerate(docs):
        if key not in d or _is_effectively_empty(d[key]):
            continue
        v = d[key]
        # try to find matching cluster
        for c_val, indices in clusters:
            if v == c_val:
                indices.append(idx)
                break
        else:
            # no matching cluster
            clusters.append((v, [idx]))

    if not clusters:
        return None

    c_val, indices = max(clusters, key=lambda pair: len(pair[1]))
    if len(indices) < min_resources:
        return None

    return c_val, indices


def collect_common_resource_fields(
    base_dir: Union[str, Path],
    dataset_id: str,
    *,
    keys: Iterable[str] = ("context", "spatial", "temporal", "sources", "licenses", "contributors"),
    min_resources: int = 2,
) -> None:
    """
    Hoist common top-level fields from resource YAMLs into the dataset template.

    Rules (per key):
      - Look at resources/<dataset_id>/*.resource.yaml
      - Ignore resources where the value is 'effectively empty'.
      - Group non-empty values by structural equality (==).
      - Pick the value that occurs most often.
      - If it appears in at least `min_resources` resources:
          * write that key/value into datasets/<id>.template.yaml
          * delete that key from any resource that has that value.

    This allows scenarios like:
      - 9 resources share the same `context`, 1 has a special `context`:
        -> shared one goes to template, 9 resources drop `context`,
           the special one keeps its own.
    """
    base = Path(base_dir)
    res_dir = base / "resources" / dataset_id
    template_path = base / "datasets" / f"{dataset_id}.template.yaml"

    if not res_dir.exists() or not template_path.exists():
        return

    resource_paths = sorted(res_dir.glob("*.resource.yaml"))
    if not resource_paths:
        return

    docs = [load_yaml(p) for p in resource_paths]
    adjusted = [deepcopy(d) for d in docs]
    common: dict[str, object] = {}

    for key in keys:
        result = _find_common_value_for_key(docs, key, min_resources=min_resources)
        if result is None:
            continue

        c_val, indices = result
        common[key] = c_val

        # delete that key from those resources that have this common value
        for i in indices:
            if key in adjusted[i] and adjusted[i][key] == c_val:
                del adjusted[i][key]

    if not common:
        return

    # merge common values into template
    tmpl = load_yaml(template_path)
    for k, v in common.items():
        tmpl[k] = v

    template_path.write_text(
        yaml.safe_dump(tmpl, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    # write back updated resources
    for p, doc in zip(resource_paths, adjusted):
        p.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
