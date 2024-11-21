"""Tests for OMIs `base` package."""

import pytest

from omi import base, validation


def deactivate_test_metadata_from_oep():
    """Test metadata from OEP."""
    metadata = base.get_metadata_from_oep_table("omi_test_table_meta_v16", oep_schema="sandbox")
    validation.validate_metadata(metadata)


def test_metadata_from_oep_non_existing_table():
    """Test error for non existing table."""
    with pytest.raises(
        base.MetadataError,
        match="Could not retrieve metadata from OEP table 'model_draft.non_existing_table'.",
    ):
        base.get_metadata_from_oep_table("non_existing_table")


def deactivate_test_metadata_from_oep_empty():
    """Test error for empty metadata."""
    with pytest.raises(
        base.MetadataError,
        match="Metadata from 'model_draft.bnetza_eeg_anlagenstammdaten_wind_classification' is empty.",
    ):
        base.get_metadata_from_oep_table("bnetza_eeg_anlagenstammdaten_wind_classification")
