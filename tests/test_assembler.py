"""
Assembly integration tests for split-files OEMetadata authoring.

This module exercises the public assembler entry point by building a small
on-disk YAML tree, applying a template, and verifying the merged OEMetadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

# We test the public assembler entry point
from omi.creation.assembler import assemble_many_metadata, assemble_metadata_dict

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


# ---------- helpers ----------


def write_yaml(p: Path, data: object) -> None:
    """Write `data` (any YAML-serializable object) to path `p`."""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


class FakeCreator:
    """
    Minimal stand-in for OEMetadataCreator used via monkeypatching.

    It mimics `generate_metadata(dataset, resources)` and skips validation.
    The constructor accepts the OEMetadata version to embed in metaMetadata.
    """

    def __init__(self, oem_version: str = "OEMetadata-2.0") -> None:
        """Initialize the fake creator with a specific OEMetadata version."""
        self.oem_version = oem_version

    def generate_metadata(self, dataset: dict, resources: list[dict]) -> dict:
        """Return a small OEMetadata-like dict sufficient for assertions."""
        return {
            "@context": "https://example.org/context.json",
            **dataset,
            "resources": resources,
            "metaMetadata": {"metadataVersion": self.oem_version},
        }


# ---------- tests ----------


def test_assemble_by_convention_with_template_merge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Assemble via convention and verify deep merge semantics.

    Asserts:
    - dataset is loaded from datasets/{id}.dataset.yaml
    - template is applied deeply (resource wins on conflicts)
    - keywords are concatenated (resource first, then template-only)
    - licenses remain resource-provided if present (no concat by default)
    - creator is invoked and returns a full dict
    """
    # dataset
    write_yaml(
        tmp_path / "datasets" / "demo.dataset.yaml",
        {
            "version": "OEMetadata-2.0.4",
            "dataset": {"name": "demo", "title": "Demo", "description": "Demo dataset"},
        },
    )

    # template
    write_yaml(
        tmp_path / "datasets" / "demo.template.yaml",
        {
            "context": {"publisher": "OEP", "contact": "a@b"},
            "keywords": ["k1"],
            "topics": ["model_draft"],
            "languages": ["en-GB"],
            "licenses": [{"name": "L1"}],  # applies only if resource doesn't provide licenses
        },
    )

    # resources
    write_yaml(
        tmp_path / "resources" / "demo" / "r1.resource.yaml",
        {
            "name": "r1",
            "title": "R1",
            # overrides nested key, should still inherit contact from template
            "context": {"publisher": "Other"},
            # resource provides its own licenses -> should NOT be concatenated by default
            "licenses": [{"name": "R1-license"}],
            # own keywords -> should concat with template keywords
            "keywords": ["r1k"],
        },
    )
    write_yaml(
        tmp_path / "resources" / "demo" / "r2.resource.yaml",
        {
            "name": "r2",
            "title": "R2",
            # no licenses provided -> should get template licenses
        },
    )

    # Patch the creator used inside assembler to our Fake
    monkeypatch.setattr("omi.creation.assembler.OEMetadataCreator", FakeCreator)

    md = assemble_metadata_dict(tmp_path, "demo")

    # dataset propagated
    assert md["name"] == "demo"
    assert md["title"] == "Demo"

    # resources present
    assert isinstance(md["resources"], list)
    assert len(md["resources"]) == 2
    r1, r2 = md["resources"]

    # deep merge for context: resource wins on conflicts, template fills missing keys
    assert r1["context"]["publisher"] == "Other"
    assert r1["context"]["contact"] == "a@b"

    # keywords/topics/languages concatenate (resource first, then template-only)
    assert r1["keywords"] == ["r1k", "k1"]
    # topics/languages inherited if missing
    assert r1["topics"] == ["model_draft"]
    assert r1["languages"] == ["en-GB"]

    # licenses: resource list wins (no concat by default)
    assert r1["licenses"] == [{"name": "R1-license"}]

    # r2 inherits licenses from template (since none provided)
    assert r2["licenses"] == [{"name": "L1"}]
    # r2 inherits keywords/topics/languages from template
    assert r2["keywords"] == ["k1"]
    assert r2["topics"] == ["model_draft"]
    assert r2["languages"] == ["en-GB"]

    # metaMetadata present from FakeCreator (assembler passes through the version)
    assert md["metaMetadata"]["metadataVersion"] == "OEMetadata-2.0.4"


def test_assemble_with_index_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assemble using an explicit metadata_index.yaml mapping."""
    base = tmp_path

    # index mapping
    write_yaml(
        base / "metadata_index.yaml",
        {
            "datasets": {
                "pp": {
                    "dataset": "datasets/powerplants.dataset.yaml",
                    "template": "datasets/powerplants.template.yaml",
                    "resources": [
                        "resources/powerplants/a.resource.yaml",
                        "resources/powerplants/b.resource.yaml",
                    ],
                },
            },
        },
    )

    write_yaml(
        base / "datasets" / "powerplants.dataset.yaml",
        {"dataset": {"name": "pp", "title": "PP"}},
    )
    write_yaml(
        base / "datasets" / "powerplants.template.yaml",
        {"keywords": ["t-k"]},
    )
    write_yaml(
        base / "resources" / "powerplants" / "a.resource.yaml",
        {"name": "a", "title": "A", "keywords": ["a-k"]},
    )
    write_yaml(
        base / "resources" / "powerplants" / "b.resource.yaml",
        {"name": "b", "title": "B"},
    )

    monkeypatch.setattr("omi.creation.assembler.OEMetadataCreator", FakeCreator)

    # Use the index explicitly
    md = assemble_metadata_dict(base, "pp", index_file=base / "metadata_index.yaml")

    assert md["name"] == "pp"
    names = [r["name"] for r in md["resources"]]
    assert names == ["a", "b"]

    # keywords concatenated for 'a', inherited for 'b'
    r_a = md["resources"][0]
    r_b = md["resources"][1]
    assert r_a["keywords"] == ["a-k", "t-k"]
    assert r_b["keywords"] == ["t-k"]


def test_assemble_many_metadata_convention_as_dict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assemble all datasets by convention; expect a dict keyed by dataset id."""
    # Dataset A
    write_yaml(
        tmp_path / "datasets" / "a.dataset.yaml",
        {"version": "OEMetadata-2.0.4", "dataset": {"name": "a", "title": "A"}},
    )
    write_yaml(
        tmp_path / "resources" / "a" / "r1.resource.yaml",
        {"name": "r1", "title": "R1"},
    )

    # Dataset B (with template)
    write_yaml(
        tmp_path / "datasets" / "b.dataset.yaml",
        {"version": "OEMetadata-2.0.4", "dataset": {"name": "b", "title": "B"}},
    )
    write_yaml(
        tmp_path / "datasets" / "b.template.yaml",
        {"keywords": ["tk"]},
    )
    write_yaml(
        tmp_path / "resources" / "b" / "r2.resource.yaml",
        {"name": "r2", "title": "R2", "keywords": ["rk"]},
    )

    # Use the FakeCreator inside the assembler
    monkeypatch.setattr("omi.creation.assembler.OEMetadataCreator", FakeCreator)

    out = assemble_many_metadata(tmp_path)  # dict[str, dict]
    # discover_dataset_ids returns sorted ids
    assert list(out.keys()) == ["a", "b"]

    # Dataset A checks
    md_a = out["a"]
    assert md_a["name"] == "a"
    assert [r["name"] for r in md_a["resources"]] == ["r1"]

    # Dataset B checks (template applied with concat)
    md_b = out["b"]
    assert md_b["name"] == "b"
    r2 = md_b["resources"][0]
    assert r2["name"] == "r2"
    assert r2["keywords"] == ["rk", "tk"]


def test_assemble_many_metadata_with_index_as_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assemble all datasets declared in index; expect a list of (id, md) pairs sorted by id."""
    base = tmp_path

    # Index with two datasets (note: keys will be sorted by helper)
    write_yaml(
        base / "metadata_index.yaml",
        {
            "datasets": {
                "x": {
                    "dataset": "datasets/x.dataset.yaml",
                    "resources": ["resources/x/x1.resource.yaml"],
                },
                "y": {
                    "dataset": "datasets/y.dataset.yaml",
                    "template": "datasets/y.template.yaml",
                    "resources": ["resources/y/y1.resource.yaml"],
                },
            },
        },
    )

    # Dataset x
    write_yaml(base / "datasets" / "x.dataset.yaml", {"dataset": {"name": "x", "title": "X"}})
    write_yaml(base / "resources" / "x" / "x1.resource.yaml", {"name": "x1"})

    # Dataset y (with template)
    write_yaml(base / "datasets" / "y.dataset.yaml", {"dataset": {"name": "y", "title": "Y"}})
    write_yaml(base / "datasets" / "y.template.yaml", {"keywords": ["t"]})
    write_yaml(base / "resources" / "y" / "y1.resource.yaml", {"name": "y1", "keywords": ["r"]})

    monkeypatch.setattr("omi.creation.assembler.OEMetadataCreator", FakeCreator)

    pairs = assemble_many_metadata(
        base,
        index_file=base / "metadata_index.yaml",
        as_dict=False,
    )  # list[tuple[str, dict]]

    # Expect sorted ids: ['x', 'y']
    ids = [ds_id for ds_id, _ in pairs]
    assert ids == ["x", "y"]

    md_x = pairs[0][1]
    md_y = pairs[1][1]

    assert md_x["name"] == "x"
    assert [r["name"] for r in md_x["resources"]] == ["x1"]

    # Template concat for y
    r_y1 = md_y["resources"][0]
    assert r_y1["keywords"] == ["r", "t"]
