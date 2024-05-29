"""Conversion module for OMI to update metadata to different versions."""

from omi.base import extract_metadata_version

METADATA_CONVERSION_CHAIN = {"OEP": ["OEP-1.5.2", "OEP-1.6.0"], "INSPIRE": []}


def convert_metadata(metadata: dict, target_version: str) -> dict:
    """
    Convert metadata to target version.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary
    target_version: str
        Target version to convert

    Returns
    -------
    dict
        Updated metadata
    """
    metadata_version = extract_metadata_version(metadata)
    metadata_conversion_functions = {
        ("OEP-1.5.2", "OEP-1.6.0"): __convert_oep_152_to_160,
    }
    metadata_conversion_function = metadata_conversion_functions[(metadata_version, target_version)]
    return metadata_conversion_function(metadata)


def __convert_oep_152_to_160(metadata: dict) -> dict:
    """
    Convert metadata with version "OEP-1.5.2" to "OEP-1.6.0".

    Parameters
    ----------
    metadata: dict
        Metadata

    Returns
    -------
    dict
        Updated metadata
    """
    # No changes in metadata fields
    metadata["metaMetadata"]["metadataVersion"] = "OEP-1.6.0"
    return metadata
