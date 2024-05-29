"""Tests for validation module of OMI."""

import pytest

from omi import validation


def test_metadata_schema_for_oep_version():
    """Test schema, template and example for OEP metadata."""
    version = "OEP-1.5.2"
    schema = validation.get_metadata_schema(version)
    assert schema.schema["description"] == "Open Energy Plaftorm (OEP) metadata schema v1.5.2"
    assert schema.template["name"] is None
    assert schema.example["name"] == "oep_metadata_table_example_v152"


def test_metadata_schema_not_found():
    """Test failing schema for invalid metadata version."""
    with pytest.raises(ValueError, match="Metadata format for metadata version OEP-1.5.0 could not be found."):
        validation.get_metadata_schema("OEP-1.5.0")
