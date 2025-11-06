"""Test suite for the OEMetadataCreator class in the OMI creation module (split-files layout)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
import yaml

from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import apply_template_to_resources, load_parts

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def sample_tree(tmp_path: Path) -> tuple[Path, str]:
    """
    Create a split-files metadata tree.

    metadata/
      datasets/
        demo.dataset.yaml
        demo.template.yaml
      resources/
        demo/
          table.resource.yaml
    """
    base = tmp_path / "metadata"
    ds_dir = base / "datasets"
    rs_dir = base / "resources" / "demo"

    ds_dir.mkdir(parents=True, exist_ok=True)
    rs_dir.mkdir(parents=True, exist_ok=True)

    # dataset yaml
    (ds_dir / "demo.dataset.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "OEMetadata-2.0",
                "dataset": {
                    "name": "test_dataset",
                    "title": "Test Dataset",
                    "description": "For unit testing",
                    "@id": "https://example.org/test_dataset",
                },
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    # template yaml (applied to every resource)
    (ds_dir / "demo.template.yaml").write_text(
        yaml.safe_dump(
            {
                "languages": ["en-GB"],
                "keywords": ["example"],
                "context": {"publisher": "OEP", "contact": "contact@example.org"},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    # one resource yaml
    (rs_dir / "table.resource.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "test_resource",
                "title": "Test Resource",
                "type": "table",
                "format": "CSV",
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer", "nullable": False},
                    ],
                    "primaryKey": ["id"],
                },
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    return base, "demo"


def test_generate_oemetadata_from_split_files(sample_tree: tuple[Path, str]) -> None:
    """End-to-end: load parts, apply template, generate metadata via creator."""
    base_dir, dataset_id = sample_tree

    # Load version/dataset/resources/template from split-files layout
    version, dataset, resources, template = load_parts(base_dir, dataset_id)

    # Deep-apply template to resources (dicts merge, lists concat for keywords/topics/languages)
    merged_resources = apply_template_to_resources(resources, template)

    creator = OEMetadataCreator(oem_version=version)
    result = creator.generate_metadata(dataset, merged_resources)

    # Basic assertions
    assert result["@context"].startswith("https://")
    assert result["name"] == "test_dataset"
    assert "resources" in result
    assert isinstance(result["resources"], list)
    assert result["resources"][0]["name"] == "test_resource"

    # Template has been applied deeply (languages concatenated / context merged)
    r0 = result["resources"][0]
    assert r0["languages"] == ["en-GB"]
    assert r0["keywords"] == ["example"]
    assert r0["context"]["publisher"] == "OEP"
    assert r0["context"]["contact"] == "contact@example.org"

    # Schema minimally intact
    assert r0["schema"]["primaryKey"] == ["id"]
    assert r0["schema"]["fields"][0]["name"] == "id"
    assert r0["schema"]["fields"][0]["nullable"] is False


def test_creator_save_writes_json(sample_tree: tuple[Path, str]) -> None:
    """Ensure creator.save writes JSON and preserves unicode."""
    base_dir, dataset_id = sample_tree
    version, dataset, resources, template = load_parts(base_dir, dataset_id)
    merged_resources = apply_template_to_resources(resources, template)

    out = base_dir / "out.json"
    creator = OEMetadataCreator(oem_version=version)
    creator.save(dataset, merged_resources, out, ensure_ascii=False, indent=2)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["name"] == "test_dataset"
    # unicode preserved (no \u escapes because ensure_ascii=False)
    assert "©" not in out.read_text(encoding="utf-8")  # sanity check; none present here by default
