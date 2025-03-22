"""Base functionality for OMI."""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass

import requests
from oemetadata.v1 import v152, v160
from oemetadata.v2 import v20

from .settings import OEP_URL

# Order matters! First entry equals latest version of metadata format
METADATA_FORMATS = {"OEP": ["OEMetadata-2.0", "OEP-1.6.0", "OEP-1.5.2"], "INSPIRE": []}
METADATA_VERSIONS = {version: md_format for md_format, versions in METADATA_FORMATS.items() for version in versions}


class MetadataError(Exception):
    """Raised when a metadata error is encountered."""


@dataclass
class MetadataSpecification:
    """Metadata schema class, holding JSON schema and (optional) template and example for given schema."""

    schema: dict
    template: dict | None = None
    example: dict | None = None


def get_metadata_from_oep_table(oep_table: str, oep_schema: str = "model_draft") -> dict:
    """
    Get metadata from OEP table.

    Parameters
    ----------
    oep_table: str
        OEP table name
    oep_schema: str
        OEP schema name

    Returns
    -------
    dict
        Metadata in OEMetadata format
    """
    response = requests.get(f"{OEP_URL}/api/v0/schema/{oep_schema}/tables/{oep_table}/meta/", timeout=90)
    if response.status_code != requests.codes.ok:
        raise MetadataError(f"Could not retrieve metadata from OEP table '{oep_schema}.{oep_table}'.")
    metadata = response.json()
    if not metadata:
        raise MetadataError(f"Metadata from '{oep_schema}.{oep_table}' is empty.")
    return metadata


def get_metadata_version(metadata: dict) -> str:
    """
    Extract metadata version from metadata.

    Parameters
    ----------
    metadata: dict
        Metadata

    Returns
    -------
    str
        Metadata version as string
    """
    # For OEP metadata
    try:
        return __normalize_metadata_version(metadata["metaMetadata"]["metadataVersion"])
    except KeyError:
        pass
    msg = "Could not extract metadata version from metadata."
    raise MetadataError(msg)


def __normalize_metadata_version(version: str) -> str:
    """
    Normalize a metadata version string by stripping patch numbers.

    For example, "OEMetadata-2.0.4" becomes "OEMetadata-2.0".
    """
    if not isinstance(version, str):
        raise MetadataError(f"Metadata version must be a string, not {type(version)}.")
    # This regex captures "OEMetadata-2.0" from "OEMetadata-2.0.4" or similar
    m = re.match(r"^(OEMetadata-2\.\d+)(?:\.\d+)?$", version)
    if m:
        return m.group(1)
    return version


def get_latest_metadata_version(metadata_format: str) -> str:
    """
    Return the latest metadata version of a given metadata format.

    Parameters
    ----------
    metadata_format: str
        Metadata format to check for latest version

    Raises
    ------
    MetadataError
        if metadata format is unknown or has no latest version

    Returns
    -------
    str
        Latest version of metadata format
    """
    if metadata_format not in METADATA_FORMATS:
        raise MetadataError(
            f"Unknown metadata format: {metadata_format}. Possible candidates are: {','.join(METADATA_FORMATS)}.",
        )
    if len(METADATA_FORMATS[metadata_format]) == 0:
        raise MetadataError(f"No latest metadata version found for format {metadata_format}.")
    return METADATA_FORMATS[metadata_format][0]


def get_metadata_specification(metadata_version: str) -> MetadataSpecification:
    """
    Return metadata specification for given metadata version.

    Metadata versions are defined in METADATA_FORMATS.
    Fetching metadata specification depends on metadata format.

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
    MetadataSpecification
        Metadata specification holding (at least) JSON schema for given metadata version.
    """
    if metadata_version not in METADATA_VERSIONS:
        raise MetadataError(f"Metadata format for metadata version {metadata_version} could not be found.")
    metadata_format = METADATA_VERSIONS[metadata_version]

    return METADATA_SPECIFICATIONS[metadata_format](metadata_version)


def __get_metadata_specs_for_oep(metadata_version: str) -> MetadataSpecification:
    """
    Return OEP metadata schema for given metadata version.

    Parameters
    ----------
    metadata_version: str
        Metadata version

    Returns
    -------
    MetadataSpecification
        Metadata schema for given metadata version including template and example.
    """
    metadata_modules = {"OEP-1.5.2": v152, "OEP-1.6.0": v160, "OEMetadata-2.0": v20}
    metadata_module = metadata_modules[metadata_version]
    module_path = pathlib.Path(metadata_module.__file__).parent
    specs = {}
    for item in ("schema", "template", "example"):
        with (module_path / f"{item}.json").open("r") as f:
            specs[item] = json.loads(f.read())
    return MetadataSpecification(**specs)


METADATA_SPECIFICATIONS = {"OEP": __get_metadata_specs_for_oep}
