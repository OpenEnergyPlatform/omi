"""Tests for validation module of OMI."""

import json
import pathlib
import re

import pytest

from omi import base, license, validation

TEST_VALIDATION_DATA_PATH = pathlib.Path(__file__).parent / "test_data" / "validation"
INVALID_METADAT_PATH = TEST_VALIDATION_DATA_PATH / "invalid_metadata"

UNSUPPORTED_OEP_METADATA_EXAMPLE_FILE = TEST_VALIDATION_DATA_PATH / "unsupported_oep_metadata_example.json"


def test_validation_of_oep_metadata():
    """Test successful validation of OEP metadata."""
    versions = ("OEP-1.5.2", "OEP-1.6.0")
    for version in versions:
        metadata_schema = base.get_metadata_specification(version)
        validation.validate_metadata(metadata_schema.example)


def test_invalid_oep_metadata():
    """Test if validation error is raised for different invalid OEP metadata."""
    with (INVALID_METADAT_PATH / "additional_key.json").open("r") as f:
        invalid_oep_metadata = json.load(f)
        # `re.escape` must be used, otherwise quotes around 'universe' are not detected correctly
        with pytest.raises(
            validation.ValidationError,
            match=re.escape("Additional properties are not allowed ('universe' was unexpected)"),
        ):
            validation.validate_metadata(invalid_oep_metadata)

    with (INVALID_METADAT_PATH / "missing_fields.json").open("r") as f:
        invalid_oep_metadata = json.load(f)
        with pytest.raises(
            license.LicenseError,
            match=r"No license information available in the metadata for resource: \d+\.?",
        ):
            validation.validate_metadata(invalid_oep_metadata)

    with (INVALID_METADAT_PATH / "wrongly_placed_null_value.json").open("r") as f:
        invalid_oep_metadata = json.load(f)
        with pytest.raises(validation.ValidationError, match="None is not of type 'object'"):
            validation.validate_metadata(invalid_oep_metadata)


def test_invalid_oep_metadata_caused_by_invalid_json():
    """Test if validation error is raised for invalid OEP metadata due to invalid JSOn syntax."""
    with (INVALID_METADAT_PATH / "duplicate_key.json").open("r") as f:
        invalid_metadata_string = f.read()
        with pytest.raises(validation.ValidationError, match="Duplicate keys in metadata: 'description'"):
            validation.validate_metadata(invalid_metadata_string)

    with (INVALID_METADAT_PATH / "wrong_json_syntax.json").open("r") as f:
        invalid_metadata_string = f.read()
        with pytest.raises(validation.ValidationError, match="Failed to decode JSON: Expecting value"):
            validation.validate_metadata(invalid_metadata_string)

    with (INVALID_METADAT_PATH / "wrong_nesting.json").open("r") as f:
        invalid_metadata_string = f.read()
        with pytest.raises(
            validation.ValidationError,
            match="Failed to decode JSON: Expecting property name enclosed in double quotes",
        ):
            validation.validate_metadata(invalid_metadata_string)

    with (INVALID_METADAT_PATH / "wrong_structure.json").open("r") as f:
        invalid_metadata_string = f.read()
        with pytest.raises(validation.ValidationError, match="Failed to decode JSON: Expecting ',' delimiter"):
            validation.validate_metadata(invalid_metadata_string)


def test_unsupported_oep_metadata_version():
    """Test if validation error is raised for unsupported OEP metadata version."""
    with UNSUPPORTED_OEP_METADATA_EXAMPLE_FILE.open("r") as f:
        unsupported_oep_metadata = json.load(f)
    with pytest.raises(
        base.MetadataError,
        match="Metadata format for metadata version OEP-1.5.1 could not be found.",
    ):
        validation.validate_metadata(unsupported_oep_metadata)


def test_metadata_schema_for_oep_version():
    """Test schema, template and example for OEP metadata."""
    version = "OEP-1.5.2"
    schema = base.get_metadata_specification(version)
    assert schema.schema["description"] == "Open Energy Platform (OEP) metadata schema v1.5.2"
    assert schema.template["name"] is None
    assert schema.example["name"] == "oep_metadata_table_example_v152"


def test_metadata_schema_not_found():
    """Test failing schema for invalid metadata version."""
    with pytest.raises(
        base.MetadataError,
        match="Metadata format for metadata version OEP-1.5.0 could not be found.",
    ):
        base.get_metadata_specification("OEP-1.5.0")


def deactivate__test_metadata_against_oep_table():
    """Test OEP table definition against OEP metadata."""
    table = "x2x_p2gas_soec_1"
    with (TEST_VALIDATION_DATA_PATH / "metadata_oep_validation.json").open("r") as f:
        metadata = json.load(f)
    validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft", metadata=metadata)


def test_metadata_against_oep_table_using_metadata_from_oep():
    """Test OEP table definition against OEP metadata, where metadata is taken from OEP."""
    table = "x2x_p2gas_soec_1"
    with pytest.raises(validation.ValidationError, match="None is not of type 'object'"):
        validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft")


def test_metadata_against_oep_table_invalid_name():
    """Test different naming convention violation for OEP metadata."""
    table = "x2x_p2gas_soec_1"
    with (TEST_VALIDATION_DATA_PATH / "metadata_oep_validation.json").open("r") as f:
        metadata = json.load(f)
    metadata["resources"][0]["name"] = "invalid"
    with pytest.raises(
        validation.ValidationError,
        match=f"Name 'invalid' of metadata resource does not fit to oep table name. "
        f"It should be one of '{table}', or 'model_draft.{table}'.",
    ):
        validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft", metadata=metadata)
    del metadata["resources"][0]["name"]
    with pytest.raises(validation.ValidationError, match="Metadata resource has no name."):
        validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft", metadata=metadata)


def test_metadata_against_oep_table_with_missing_fields():
    """Test error raised for missing fields."""
    table = "x2x_p2gas_soec_1"
    with (TEST_VALIDATION_DATA_PATH / "metadata_oep_validation.json").open("r") as f:
        metadata = json.load(f)
    metadata["resources"][0]["schema"]["fields"].append({"name": "added_field", "type": "string"})
    with pytest.raises(validation.ValidationError, match="Field 'added_field' not defined in OEP table"):
        validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft", metadata=metadata)
    metadata["resources"][0]["schema"]["fields"].pop()
    metadata["resources"][0]["schema"]["fields"].pop()
    with pytest.raises(
        validation.ValidationError,
        match=f"Field 'comment' from OEP table 'model_draft.{table}' is missing in metadata schema.",
    ):
        validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft", metadata=metadata)


def test_metadata_against_oep_table_with_incompatible_field_types():
    """Test error raised for incompatible field types."""
    table = "x2x_p2gas_soec_1"
    with (TEST_VALIDATION_DATA_PATH / "metadata_oep_validation.json").open("r") as f:
        metadata = json.load(f)
    metadata["resources"][0]["schema"]["fields"][0]["type"] = "string"
    with pytest.raises(
        validation.ValidationError,
        match="Field type 'bigint' from OEP table field 'id' differs from type 'string' defined in metadata schema.",
    ):
        validation.validate_oep_table_against_metadata(oep_table=table, oep_schema="model_draft", metadata=metadata)
