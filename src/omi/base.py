"""Base functionality for OMI."""

from __future__ import annotations


class MetadataError(Exception):
    """Raised when a metadata error is encountered."""


def extract_metadata_version(metadata: dict) -> str:
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
        return metadata["metaMetadata"]["metadataVersion"]
    except KeyError:
        pass
    msg = "Could not extract metadata version from metadata."
    raise MetadataError(msg)
