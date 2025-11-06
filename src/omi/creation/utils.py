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
    from collections.abc import Hashable

# --- deep merge helpers -------------------------------------------------------

# List keys we concatenate (resource + template) instead of replacing.
DEFAULT_CONCAT_LIST_KEYS = {"keywords", "topics", "languages"}


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
    - Dicts are deep-merged (resource wins on conflicts).
    - Lists are concatenated only for keys in `concat_list_keys`; otherwise, the
      resource list is preserved as-is.
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
        if isinstance(rval, dict) and isinstance(tval, dict):
            result[key] = deep_apply_template_to_resource(rval, tval, concat_list_keys)
            continue

        if isinstance(rval, list) and isinstance(tval, list):
            if key in concat_list_keys:
                result[key] = _merge_lists(tval, rval, deduplicate=True)
            # else: resource list stays as-is
            continue
        # scalar: resource value stays
    return result


def apply_template_to_resources(
    resources: list[dict[str, object]],
    template: dict[str, object],
) -> list[dict[str, object]]:
    """Apply the same `template` to each resource in `resources`."""
    if not template:
        return resources
    return [deep_apply_template_to_resource(r, template) for r in resources]


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
    """
    dataset_path, template_path, resource_paths = resolve_from_index(base_dir, dataset_id, index_file)

    if dataset_path is None or not dataset_path.exists():
        raise FileNotFoundError(f"Dataset YAML not found for '{dataset_id}'")

    dataset_yaml = load_yaml(dataset_path)
    version = str(dataset_yaml.get("version", "OEMetadata-2.0.4"))
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
    """
    idx_path = Path(index_file)
    if not idx_path.exists():
        return []
    with idx_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    ds = data.get("datasets") or {}
    return sorted(ds.keys())
