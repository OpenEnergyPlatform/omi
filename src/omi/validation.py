"""Validation module for OMI."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

import jsonschema
from metadata import v152, v160

from omi.base import extract_metadata_version

# Order matters! First entry equals latest version of metadata format
METADATA_FORMATS = {"OEP": ["OEP-1.6.0", "OEP-1.5.2"], "INSPIRE": []}
METADATA_VERSIONS = {version: md_format for md_format, versions in METADATA_FORMATS.items() for version in versions}


class ValidationError(Exception):
    """Exception raised when a validation fails."""


@dataclass
class MetadataSchema:
    """Metadata schema class, holding JSON schema and (optional) template and example for given schema."""

    schema: dict
    template: dict | None = None
    example: dict | None = None


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
    metadata_schema = get_metadata_schema(metadata_version)
    jsonschema.validate(metadata, metadata_schema.schema)


def get_metadata_schema(metadata_version: str) -> MetadataSchema:
    """
    Return metadata schema for given metadata version.

    Metadata versions are defined in METADATA_FORMATS.
    Fetching metadata schema depends on metadata format.

    Parameters
    ----------
    metadata_version: str
        Metadata version

    Raises
    ------
    ValueError
        if metadata version is not in METADATA_FORMATS

    Returns
    -------
    MetadataSchema
        Metadata schema holding (at least) JSON schema for given metadata version.
    """
    if metadata_version not in METADATA_VERSIONS:
        raise ValidationError(f"Metadata format for metadata version {metadata_version} could not be found.")
    metadata_format = METADATA_VERSIONS[metadata_version]

    return METADATA_SCHEMAS[metadata_format](metadata_version)


def __get_metadata_schema_for_oep(metadata_version: str) -> MetadataSchema:
    """
    Return OEP metadata schema for given metadata version.

    Parameters
    ----------
    metadata_version: str
        Metadata version

    Returns
    -------
    MetadataSchema
        Metadata schema for given metadata version including template and example.
    """
    metadata_modules = {"OEP-1.5.2": v152, "OEP-1.6.0": v160}
    metadata_module = metadata_modules[metadata_version]
    module_path = pathlib.Path(metadata_module.__file__).parent
    schema = {}
    for item in ("schema", "template", "example"):
        with (module_path / f"{item}.json").open("r") as f:
            schema[item] = json.loads(f.read())
    return MetadataSchema(**schema)


METADATA_SCHEMAS = {"OEP": __get_metadata_schema_for_oep}
