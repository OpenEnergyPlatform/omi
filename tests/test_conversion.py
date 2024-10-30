"""Tests for OMIs conversion module."""

import pytest

import omi.base
from omi import base, conversion, validation


def test_conversion_from_oep_152_to_160():
    """Test conversion from OEP v1.5.2 -> v1.6.0."""
    metadata_schema_152 = omi.base.get_metadata_specification("OEP-1.5.2").example
    converted_metadata_152 = conversion.convert_metadata(metadata_schema_152, "OEP-1.6.0")
    assert base.get_metadata_version(converted_metadata_152) == "OEP-1.6.0"
    validation.validate_metadata(converted_metadata_152)


def test_conversion_from_oep_160_to_200():
    """Test conversion from OEP v1.6.0 -> v2.0.0."""
    metadata_schema_160 = omi.base.get_metadata_specification("OEP-1.6.0").example
    converted_metadata_160 = conversion.convert_metadata(metadata_schema_160, "OEMetadata-2.0.0")
    assert base.get_metadata_version(converted_metadata_160) == "OEMetadata-2.0.0"
    validation.validate_metadata(converted_metadata_160)


def test_conversion_chain():
    """Test conversion chain with conversion tree structure."""

    def a_b_conversion(md: dict) -> dict:
        md["metaMetadata"]["metadataVersion"] = "b"
        md["value"] = md["value"] * 2
        return md

    def a_c_conversion(md: dict) -> dict:
        md["metaMetadata"]["metadataVersion"] = "c"
        md["value"] = md["value"] * 3
        return md

    def c_d_conversion(md: dict) -> dict:
        md["metaMetadata"]["metadataVersion"] = "d"
        md["value"] = md["value"] * 4
        return md

    def c_e_conversion(md: dict) -> dict:
        md["metaMetadata"]["metadataVersion"] = "e"
        md["value"] = md["value"] * 5
        return md

    conversion.METADATA_CONVERSIONS[("a", "b")] = a_b_conversion
    conversion.METADATA_CONVERSIONS[("a", "c")] = a_c_conversion
    conversion.METADATA_CONVERSIONS[("c", "d")] = c_d_conversion
    conversion.METADATA_CONVERSIONS[("c", "e")] = c_e_conversion

    # Create dummy metadata in OEP format with version "a"
    metadata = {"name": "a", "value": 10, "metaMetadata": {"metadataVersion": "a"}}
    converted_metadata = conversion.convert_metadata(metadata, "e")
    assert base.get_metadata_version(converted_metadata) == "e"
    assert converted_metadata["value"] == 10 * 3 * 5


def test_invalid_conversion():
    """Test if conversion error is raised for invalid conversion chain."""
    metadata = {"metaMetadata": {"metadataVersion": "OEP-1.5.2"}}
    with pytest.raises(conversion.ConversionError, match="No conversion chain found from OEP-1.5.2 to OEP-1.5.0."):
        conversion.convert_metadata(metadata, "OEP-1.5.0")
