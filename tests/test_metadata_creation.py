"""Test suite for the OEMetadataCreator class in the OMI creation module."""

from pathlib import Path

import pytest
import yaml

from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import load_yaml_metadata


@pytest.fixture()
def sample_yaml(tmp_path: Path) -> Path:
    """Fixture to create a sample YAML file for testing."""
    content = {
        "version": "OEMetadata-2.0.4",
        "dataset": {
            "name": "test_dataset",
            "title": "Test Dataset",
            "description": "For unit testing",
            "@id": "https://example.org/test_dataset",
        },
        "template": {"languages": ["en-GB"]},
        "resources": [{"name": "test_resource", "title": "Test Resource", "format": "CSV", "type": "table"}],
    }

    file_path = tmp_path / "metadata.yaml"
    with Path.open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(content, f, sort_keys=False)

    return file_path


def test_generate_oemetadata(sample_yaml: Path) -> None:
    """Test the generation of OEMetadata from a sample YAML file."""
    version, dataset, resources = load_yaml_metadata(sample_yaml)
    creator = OEMetadataCreator()

    result = creator.generate_metadata(dataset, resources)

    # Basic assertions
    assert result["@context"].startswith("https://")
    assert result["name"] == "test_dataset"
    assert "resources" in result
    assert isinstance(result["resources"], list)
    assert result["resources"][0]["name"] == "test_resource"
    assert "languages" in result["resources"][0]
