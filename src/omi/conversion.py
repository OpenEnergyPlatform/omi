"""Conversion module for OMI to update metadata to different versions."""

from __future__ import annotations

from copy import deepcopy

from omi.base import get_metadata_version
from omi.conversions.v152_to_v160 import convert_oep_152_to_160
from omi.conversions.v160_to_v20 import convert_oep_160_to_20


class ConversionError(Exception):
    """Raised when a conversion fails."""


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
    metadata_version = get_metadata_version(metadata)
    conversion_chain = __get_conversion_chain(metadata_version, target_version)
    converted_metadata = deepcopy(metadata)
    for next_version in conversion_chain[1:]:
        current_version = get_metadata_version(converted_metadata)
        converted_metadata = METADATA_CONVERSIONS[(current_version, next_version)](converted_metadata)
    return converted_metadata


def __get_conversion_chain(source_version: str, target_version: str) -> list[str]:
    """
    Try to find conversion chain from source version to target version.

    Parameters
    ----------
    source_version: str
        Starting version
    target_version: str
        Version goal

    Raises
    ------
    ConversionError
        if no conversion chain is found

    Returns
    -------
    list[str]
        List of conversion chain from source version to target version
    """

    def get_chain(current_version: str) -> list[str] | None:
        for source, target in METADATA_CONVERSIONS:
            if source != current_version:
                continue
            if target == target_version:
                # Solution found! Return last conversion tuple
                return [current_version, target_version]
            child_chain = get_chain(target)
            if child_chain is None:
                continue
            return [current_version, *child_chain]
        return None

    conversion_chain = get_chain(source_version)
    if conversion_chain:
        return conversion_chain
    raise ConversionError(f"No conversion chain found from {source_version} to {target_version}.")


METADATA_CONVERSIONS = {
    ("OEP-1.5.2", "OEP-1.6.0"): convert_oep_152_to_160,
    ("OEP-1.6.0", "OEMetadata-2.0"): convert_oep_160_to_20,
}
