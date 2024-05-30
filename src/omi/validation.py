"""Validation module for OMI."""

from __future__ import annotations

import jsonschema

from omi.base import extract_metadata_version, get_metadata_specification


class ValidationError(Exception):
    """Exception raised when a validation fails."""


def validate_metadata(metadata: dict) -> None:
    """
    Validate metadata against related metadata schema.

    Parameters
    ----------
    metadata: dict
        Metadata

    Returns
    -------
    None
        if metadata schema is valid. Otherwise it raises an exception.
    """
    metadata_version = extract_metadata_version(metadata)
    metadata_schema = get_metadata_specification(metadata_version)
    jsonschema.validate(metadata, metadata_schema.schema)
