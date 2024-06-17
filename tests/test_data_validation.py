"""Tests for validating data via OMI."""
import json
import pathlib

import pandas as pd
import pytest
from frictionless import Report

from omi import validation


def test_data_validation_against_oep():
    """Test data validation with example file against OEP table."""
    valid_data_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "hackathon_lignite_hh_valid.csv"
    valid_data = pd.read_csv(valid_data_file, delimiter=";")
    validation.validate_data(valid_data, oep_table="hackathon_com_lignite_hh", oep_schema="model_draft")


def test_data_validation_against_metadata():
    """Test data validation with example file against metadata from file."""
    valid_data_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "data.csv"
    valid_data = pd.read_csv(valid_data_file, delimiter=";")
    metadata_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "metadata_for_data_csv.json"
    with metadata_file.open("r") as f:
        metadata = json.load(f)
    validation.validate_data(valid_data, metadata=metadata)


def test_data_validation_report():
    """Test data validation with example file."""
    valid_data_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "hackathon_lignite_hh_valid.csv"
    valid_data = pd.read_csv(valid_data_file, delimiter=";")
    report = validation.validate_data(
        valid_data,
        oep_table="hackathon_com_lignite_hh",
        oep_schema="model_draft",
        return_report=True,
    )
    assert report is None


def test_data_validation_invalid():
    """Test invalid data validation with example file."""
    invalid_data_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "hackathon_lignite_hh_invalid.csv"
    invalid_data = pd.read_csv(invalid_data_file, delimiter=";")
    with pytest.raises(validation.ValidationError, match="Data validation failed."):
        validation.validate_data(invalid_data, oep_table="hackathon_com_lignite_hh", oep_schema="model_draft")


def test_data_validation_invalid_report():
    """Test invalid data validation with example file."""
    invalid_data_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "hackathon_lignite_hh_invalid.csv"
    invalid_data = pd.read_csv(invalid_data_file, delimiter=";")
    report = validation.validate_data(
        invalid_data,
        oep_table="hackathon_com_lignite_hh",
        oep_schema="model_draft",
        return_report=True,
    )
    assert isinstance(report, Report)
    assert not report.valid


def test_invalid_data():
    """Test invalid data validation with example files."""
    metadata_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "metadata_for_data_csv.json"
    with metadata_file.open("r") as f:
        metadata = json.load(f)

    invalid_data_file = (
        pathlib.Path(__file__).parent / "test_data" / "validation" / "invalid_data" / "missing_column.csv"
    )
    invalid_data = pd.read_csv(invalid_data_file, delimiter=";")
    with pytest.raises(validation.ValidationError, match="Could not find column 'method' in data."):
        validation.validate_data(invalid_data, metadata=metadata)

    invalid_data_file = pathlib.Path(__file__).parent / "test_data" / "validation" / "invalid_data" / "extra_column.csv"
    invalid_data = pd.read_csv(invalid_data_file, delimiter=";")
    with pytest.raises(validation.ValidationError, match="Could not find field 'added_column' in schema."):
        validation.validate_data(invalid_data, metadata=metadata)

    invalid_data_file = (
        pathlib.Path(__file__).parent / "test_data" / "validation" / "invalid_data" / "invalid_datatype.csv"
    )
    invalid_data = pd.read_csv(invalid_data_file, delimiter=";")
    with pytest.raises(validation.ValidationError, match="type-error"):
        validation.validate_data(invalid_data, metadata=metadata)

    invalid_data_file = (
        pathlib.Path(__file__).parent / "test_data" / "validation" / "invalid_data" / "duplicate_primary_keys.csv"
    )
    invalid_data = pd.read_csv(invalid_data_file, delimiter=";")
    with pytest.raises(validation.ValidationError, match="primary-key"):
        validation.validate_data(invalid_data, metadata=metadata)


def test_invalid_arguments_to_validation_function():
    """Test different invalid function calls to validation function."""
    with pytest.raises(validation.ValidationError, match="Data must be given as pandas.DataFrame."):
        validation.validate_data({})
    with pytest.raises(
        validation.ValidationError,
        match="You must either set metadata or OEP table to validate data against.",
    ):
        validation.validate_data(pd.DataFrame())
    with pytest.raises(validation.ValidationError, match="Cannot validate data against both metadata and OEP table."):
        validation.validate_data(pd.DataFrame(), metadata={"a": "a"}, oep_table="a", oep_schema="a")
    with pytest.raises(validation.ValidationError, match="Cannot validate data against both metadata and OEP table."):
        validation.validate_data(pd.DataFrame(), metadata={"a": "a"}, oep_table="a")
    with pytest.raises(validation.ValidationError, match="Cannot validate data against both metadata and OEP table."):
        validation.validate_data(pd.DataFrame(), metadata={"a": "a"}, oep_schema="a")
