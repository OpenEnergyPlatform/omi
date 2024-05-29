"""Validation module for OMI."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from metadata import v152, v160

# Order matters! First entry equals latest version of metadata format
METADATA_FORMATS = {"OEP": ["OEP-1.6.0", "OEP-1.5.2"], "INSPIRE": []}
METADATA_VERSIONS = {version: md_format for md_format, versions in METADATA_FORMATS.items() for version in versions}


@dataclass
class MetadataSchema:
    """Metadata schema class, holding JSON schema and (optional) template and example for given schema."""

    schema: dict
    template: dict | None = None
    example: dict | None = None


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
        raise ValueError(f"Metadata format for metadata version {metadata_version} could not be found.")
    metadata_format = METADATA_VERSIONS[metadata_version]

    metadata_schema_functions = {"OEP": get_metadata_schema_for_oep}
    return metadata_schema_functions[metadata_format](metadata_version)


def get_metadata_schema_for_oep(metadata_version: str) -> MetadataSchema:
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
