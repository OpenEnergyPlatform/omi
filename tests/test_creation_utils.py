"""Unit tests for the OMI creation utils (templating, IO, discovery)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

# Functions under test
from omi.creation.utils import (
    DEFAULT_CONCAT_LIST_KEYS,
    _merge_lists,
    apply_template_to_resources,
    deep_apply_template_to_resource,
    discover_dataset_ids,
    discover_dataset_ids_from_index,
    discover_paths,
    load_parts,
    load_yaml,
    resolve_from_index,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------- helpers ----------


def _write_yaml(p: Path, data: object) -> None:
    """Write a YAML-serializable `data` object to `p`, creating parents."""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


# ---------- tests: list merging + deep template ----------


def test_merge_lists_deduplicates_and_respects_resource_first() -> None:
    """`_merge_lists` keeps resource-first order and de-duplicates template items."""
    resource_list = ["a", "b"]
    template_list = ["b", "c"]
    merged = _merge_lists(template_list, resource_list, deduplicate=True)
    assert merged == ["a", "b", "c"]


def test_deep_apply_template_to_resource_concat_for_keywords_topics_languages() -> None:
    """Default concat keys (keywords/topics/languages) are concatenated; others are not."""
    resource = {
        "name": "r",
        "keywords": ["rk"],
        "topics": ["rt"],
        "languages": ["rl"],
        "context": {"publisher": "R"},
        "list_no_concat": [1, 2],
    }
    template = {
        "keywords": ["tk"],
        "topics": ["tt"],
        "languages": ["tl"],
        "context": {"publisher": "T", "contact": "a@b"},
        "list_no_concat": [3, 4],
    }

    out = deep_apply_template_to_resource(resource, template)
    # concat lists for default concat keys
    assert out["keywords"] == ["rk", "tk"]
    assert out["topics"] == ["rt", "tt"]
    assert out["languages"] == ["rl", "tl"]
    # resource list wins for non-concat keys
    assert out["list_no_concat"] == [1, 2]
    # deep dict merge: resource wins on conflict, template fills missing
    assert out["context"]["publisher"] == "R"
    assert out["context"]["contact"] == "a@b"


def test_deep_apply_template_to_resource_custom_concat_keys() -> None:
    """Custom concat set allows concatenating lists like `licenses`."""
    resource = {"licenses": [{"name": "R1"}]}
    template = {"licenses": [{"name": "T1"}]}
    # By default, 'licenses' is NOT concatenated
    out_default = deep_apply_template_to_resource(resource, template)
    assert out_default["licenses"] == [{"name": "R1"}]

    # If we opt-in, it concatenates (resource first, then template-only)
    custom_keys = set(DEFAULT_CONCAT_LIST_KEYS) | {"licenses"}
    out_custom = deep_apply_template_to_resource(resource, template, concat_list_keys=custom_keys)
    assert out_custom["licenses"] == [{"name": "R1"}, {"name": "T1"}]


def test_apply_template_to_resources_applies_per_item() -> None:
    """Template is applied to each resource; concat for `keywords` by default."""
    resources = [{"name": "a"}, {"name": "b", "keywords": ["bk"]}]
    template = {"keywords": ["tk"]}
    out = apply_template_to_resources(resources, template)
    assert out[0]["keywords"] == ["tk"]  # inherited from template
    assert out[1]["keywords"] == ["bk", "tk"]  # concatenated: resource first, then template-only


# ---------- tests: YAML IO + discovery ----------


def test_load_yaml_reads_empty_as_empty_dict(tmp_path: Path) -> None:
    """Empty YAML file is read as an empty dict."""
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    data = load_yaml(p)
    assert data == {}


def test_discover_paths_and_resolve_from_index(tmp_path: Path) -> None:
    """Discovery by convention and resolution by index both return expected paths."""
    base = tmp_path
    # convention files
    ds = base / "datasets" / "powerplants.dataset.yaml"
    tp = base / "datasets" / "powerplants.template.yaml"
    rdir = base / "resources" / "powerplants"
    r1 = rdir / "a.resource.yaml"
    r2 = rdir / "b.resource.yaml"

    _write_yaml(ds, {"version": "OEMetadata-2.0.4", "dataset": {"name": "pp"}})
    _write_yaml(tp, {"keywords": ["k1"]})
    _write_yaml(r1, {"name": "a"})
    _write_yaml(r2, {"name": "b"})

    dspath, tpath, rpaths = discover_paths(base, "powerplants")
    assert dspath == ds
    assert tpath == tp
    assert rpaths == [r1, r2]

    # index mapping (deliberately flips resource order)
    idx = base / "metadata_index.yaml"
    _write_yaml(
        idx,
        {
            "datasets": {
                "powerplants": {
                    "dataset": "datasets/powerplants.dataset.yaml",
                    "template": "datasets/powerplants.template.yaml",
                    "resources": [
                        "resources/powerplants/b.resource.yaml",
                        "resources/powerplants/a.resource.yaml",
                    ],
                },
            },
        },
    )
    d2, t2, rs2 = resolve_from_index(base, "powerplants", idx)
    assert d2 == ds
    assert t2 == tp
    assert rs2 == [base / "resources/powerplants/b.resource.yaml", base / "resources/powerplants/a.resource.yaml"]


def test_load_parts_returns_all_sections(tmp_path: Path) -> None:
    """`load_parts` returns (version, dataset, resources, template) with expected contents."""
    base = tmp_path
    ds = base / "datasets" / "households.dataset.yaml"
    tp = base / "datasets" / "households.template.yaml"
    rdir = base / "resources" / "households"
    r1 = rdir / "hh1.resource.yaml"

    _write_yaml(ds, {"version": "OEMetadata-2.0.4", "dataset": {"name": "households", "title": "HH"}})
    _write_yaml(tp, {"context": {"publisher": "OEP"}})
    _write_yaml(r1, {"name": "hh1"})

    version, dataset, resources, template = load_parts(base, "households")
    assert version == "OEMetadata-2.0.4"
    assert dataset == {"name": "households", "title": "HH"}
    assert resources == [{"name": "hh1"}]
    assert template == {"context": {"publisher": "OEP"}}


def test_load_parts_raises_when_dataset_missing(tmp_path: Path) -> None:
    """`load_parts` raises FileNotFoundError if the dataset YAML is missing."""
    with pytest.raises(FileNotFoundError):
        load_parts(tmp_path, "missing")


# ---------- tests: dataset id discovery ----------


def test_discover_dataset_ids(tmp_path: Path) -> None:
    """`discover_dataset_ids` finds dataset ids by scanning datasets/*.dataset.yaml."""
    _write_yaml(tmp_path / "datasets" / "a.dataset.yaml", {"dataset": {"name": "a"}})
    _write_yaml(tmp_path / "datasets" / "b.dataset.yaml", {"dataset": {"name": "b"}})
    ids = discover_dataset_ids(tmp_path)
    assert ids == ["a", "b"]


def test_discover_dataset_ids_from_index(tmp_path: Path) -> None:
    """`discover_dataset_ids_from_index` returns top-level 'datasets' keys in index YAML."""
    idx = tmp_path / "metadata_index.yaml"
    _write_yaml(idx, {"datasets": {"x": {}, "y": {}}})
    ids = discover_dataset_ids_from_index(idx)
    assert ids == ["x", "y"]


def test_discover_dataset_ids_from_index_missing_file(tmp_path: Path) -> None:
    """Missing index file yields an empty list of dataset ids."""
    ids = discover_dataset_ids_from_index(tmp_path / "nope.yaml")
    assert ids == []
