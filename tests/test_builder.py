"""Tests for the MetadataBuilder and Schema Drift detection."""

import pytest

from omi.creation.builder import MetadataBuilder, SchemaDriftError


@pytest.fixture()
def base_metadata() -> dict:
    """Provide a sample base metadata dictionary for testing."""
    return {
        "name": "test_dataset",
        "resources": [
            {
                "name": "boundaries.test_table",
                "schema": {
                    "primaryKey": ["id"],
                    "fields": [
                        {"name": "id", "type": "integer", "description": "The ID"},
                        {"name": "geom", "type": "string", "description": "Geometry data"},
                    ],
                },
            },
        ],
    }


def test_builder_set_path_and_build(base_metadata: dict) -> None:
    """Test that set_path correctly updates a top-level metadata key."""
    builder = MetadataBuilder(base_metadata)
    builder.set_path("/publicationDate", "2025-01-01")

    result = builder.build(validate_policy="skip")
    assert result["publicationDate"] == "2025-01-01"
    assert result["name"] == "test_dataset"


def test_merge_and_diff_db_schema_no_drift(base_metadata: dict) -> None:
    """Test that merge_and_diff_db_schema succeeds and merges attributes when schemas match."""
    builder = MetadataBuilder(base_metadata)

    db_skeleton = {
        "schema": {
            "primaryKey": ["id"],
            "fields": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "geom", "type": "string", "nullable": True},
            ],
        },
    }

    report = builder.resource("boundaries.test_table").merge_and_diff_db_schema(db_skeleton)

    assert not report["missing_in_yaml"]
    assert not report["missing_in_db"]
    assert not report["type_mismatches"]

    result = builder.build(validate_policy="skip")
    fields = result["resources"][0]["schema"]["fields"]

    # DB structure (nullable) merged with YAML descriptions
    assert fields[0]["nullable"] is False
    assert fields[0]["description"] == "The ID"


def test_merge_and_diff_db_schema_with_drift(base_metadata: dict) -> None:
    """Test that missing columns in either DB or YAML are correctly detected and flagged."""
    builder = MetadataBuilder(base_metadata)

    db_skeleton = {
        "schema": {
            "primaryKey": ["id"],
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "new_column", "type": "number"},  # DB added a column, missing 'geom'
            ],
        },
    }

    report = builder.resource(0).merge_and_diff_db_schema(db_skeleton)

    assert "new_column" in report["missing_in_yaml"]
    assert "geom" in report["missing_in_db"]

    result = builder.build(validate_policy="skip")
    fields = result["resources"][0]["schema"]["fields"]

    # Check new column flagged with TODO
    new_field = next(f for f in fields if f["name"] == "new_column")
    assert "TODO:" in new_field["description"]
    assert new_field["type"] == "number"


def test_merge_and_diff_db_schema_strict_mode(base_metadata: dict) -> None:
    """Test that strict mode raises a SchemaDriftError when schema columns drift."""
    builder = MetadataBuilder(base_metadata)

    db_skeleton = {
        "schema": {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "geom", "type": "string"},
                {"name": "undocumented_column", "type": "string"},
            ],
        },
    }

    with pytest.raises(SchemaDriftError) as exc_info:
        builder.resource(0).merge_and_diff_db_schema(db_skeleton, strict=True)

    assert "undocumented_column" in str(exc_info.value)


def test_merge_and_diff_type_mismatch(base_metadata: dict) -> None:
    """Test that type mismatches are reported and DB types overwrite YAML types."""
    builder = MetadataBuilder(base_metadata)

    db_skeleton = {
        "schema": {
            "fields": [
                {"name": "id", "type": "string"},  # DB changed to string
                {"name": "geom", "type": "geometry"},  # DB changed to geometry
            ],
        },
    }

    report = builder.resource(0).merge_and_diff_db_schema(db_skeleton)

    mismatches = report["type_mismatches"]
    assert "id" in mismatches
    assert mismatches["id"]["db"] == "string"
    assert mismatches["id"]["yaml"] == "integer"

    result = builder.build(validate_policy="skip")
    fields = result["resources"][0]["schema"]["fields"]

    # DB type should overwrite YAML type!
    assert fields[0]["type"] == "string"
    assert fields[1]["type"] == "geometry"


def test_set_resource_field_descriptions(base_metadata: dict) -> None:
    """Test that field descriptions and nullability can be batch-updated for a resource."""
    builder = MetadataBuilder(base_metadata)

    builder.set_resource_field_descriptions(
        "boundaries.test_table",
        {"id": "Updated ID description"},
        default_nullable=True,
    )

    result = builder.build(validate_policy="skip")
    fields = result["resources"][0]["schema"]["fields"]

    assert fields[0]["description"] == "Updated ID description"
    assert fields[0]["nullable"] is True
