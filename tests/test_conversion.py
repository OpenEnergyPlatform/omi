"""Tests for OMIs conversion module."""

from omi import base, conversion, validation


def test_conversion_from_oep_152_to_160():
    """Test conversion from OEP v1.5.2 -> v1.6.0."""
    metadata_schema_152 = validation.get_metadata_schema("OEP-1.5.2").example
    converted_metadata_152 = conversion.convert_metadata(metadata_schema_152, "OEP-1.6.0")
    assert base.extract_metadata_version(converted_metadata_152) == "OEP-1.6.0"
    validation.validate_metadata(converted_metadata_152)
