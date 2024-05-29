"""Tests for validation module of OMI."""

import json
import pathlib

import pytest
from jsonschema.exceptions import ValidationError

from omi import validation

UNSUPPORTED_OEP_METADATA_EXAMPLE_FILE = (
    pathlib.Path(__file__).parent / "test_data" / "unsupported_oep_metadata_example.json"
)
INVALID_OEP_METADATA_EXAMPLE_FILE = pathlib.Path(__file__).parent / "test_data" / "invalid_oep_metadata_example.json"


def test_validation_of_oep_metadata():
    """Test successful validation of OEP metadata."""
    versions = ("OEP-1.5.2", "OEP-1.6.0")
    for version in versions:
        metadata_schema = validation.get_metadata_schema(version)
        validation.validate_metadata(metadata_schema.example)


def test_invalid_oep_metadata_version():
    """Test if validation error is raised for invalid OEP metadata."""
    with INVALID_OEP_METADATA_EXAMPLE_FILE.open("r") as f:
        invalid_oep_metadata = json.load(f)
    with pytest.raises(ValidationError):
        validation.validate_metadata(invalid_oep_metadata)


def test_unsupported_oep_metadata_version():
    """Test if validation error is raised for unsupported OEP metadata version."""
    with UNSUPPORTED_OEP_METADATA_EXAMPLE_FILE.open("r") as f:
        unsupported_oep_metadata = json.load(f)
    with pytest.raises(
        validation.ValidationError,
        match="Metadata format for metadata version OEP-1.5.1 could not be found.",
    ):
        validation.validate_metadata(unsupported_oep_metadata)


def test_metadata_schema_for_oep_version():
    """Test schema, template and example for OEP metadata."""
    version = "OEP-1.5.2"
    schema = validation.get_metadata_schema(version)
    assert schema.schema["description"] == "Open Energy Plaftorm (OEP) metadata schema v1.5.2"
    assert schema.template["name"] is None
    assert schema.example["name"] == "oep_metadata_table_example_v152"


def test_metadata_schema_not_found():
    """Test failing schema for invalid metadata version."""
    with pytest.raises(
        validation.ValidationError,
        match="Metadata format for metadata version OEP-1.5.0 could not be found.",
    ):
        validation.get_metadata_schema("OEP-1.5.0")
