"""Conversion functions for metadata version "OEP-1.5.2" to "OEP-1.6.0"."""


def convert_oep_152_to_160(metadata: dict) -> dict:
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
