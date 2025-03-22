"""Module to check licenses."""

import json
import re
from pathlib import Path

from omi.base import get_metadata_version

LICENCES_FILE = Path(__file__).parent / "data" / "licenses.json"


class LicenseError(Exception):
    """Exception raised when a license is invalid."""


def normalize_license_name(name: str) -> str:
    """
    Normalize license name.

    Remove '<' and '>' symbols, remove '(ODbL)', replace whitespaces with hyphens,
    and convert to uppercase.

    Parameters
    ----------
    name: str
        License name

    Returns
    -------
    str
        Normalized license name
    """
    # Remove '<' and '>' symbols.
    name = re.sub(r"[<>]", "", name)
    # Remove the specific pattern "(ODbL)".
    name = re.sub(r"\(ODbL\)", "", name)
    # Normalize extra spaces and then replace all whitespace with hyphens.
    name = re.sub(r"\s+", " ", name).strip()
    return re.sub(r"\s", "-", name).upper()


def read_licenses() -> set[str, str]:
    """
    Read license IDs from SPDX licenses.

    Returns
    -------
    set[str]
        Set of license IDs
    """
    with LICENCES_FILE.open("r", encoding="utf-8") as file:
        licenses = json.load(file)
    # Create a set of unique license ID values
    return {
        (license_info.get("licenseId").upper(), normalize_license_name(license_info.get("name").upper()))
        for license_info in licenses["licenses"]
    }


def validate_license(license_id: str) -> bool:
    """
    Validate single license ID.

    Parameters
    ----------
    license_id: str
        License ID

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    normalized_license = normalize_license_name(license_id)
    if normalized_license not in LICENSES:
        return False
    return True


def validate_oemetadata_licenses(metadata: dict) -> None:
    """
    Validate licenses in OEMetadata.

    Parameters
    ----------
    metadata: dict
        OEMetadata dictionary

    Raises
    ------
    LicenseError
        Raised if license is invalid or no license is found

    Returns
    -------
    None
        if licenses are valid, otherwise LicenseError is raised
    """
    if metadata is None:
        msg = "Metadata is empty."
        raise LicenseError(msg)

    version = get_metadata_version(metadata)
    licenses_info = _find_license_field(metadata, version)

    for resource_index, licenses in licenses_info:
        if not licenses:
            raise LicenseError(f"No license information available in the metadata for resource: {resource_index + 1}.")
        for i, license_ in enumerate(licenses or []):
            if not license_.get("name") and not license_.get("title"):
                raise LicenseError(
                    "The license name and title are missing in resource"
                    f"{resource_index + 1}, license {i + 1} ({license_}).",
                )
            name_not_found = False
            if not validate_license(license_["name"]):
                name_not_found = True

            if not name_not_found and not validate_license(license_["title"]):
                raise LicenseError(
                    f"The (normalized) license name '{license_['name']}' in resource"
                    f"{resource_index + 1}, license {i + 1} "
                    "was not found in the SPDX licenses list. "
                    "(See https://github.com/spdx/license-list-data/blob/main/json/licenses.json).",
                )


def _find_license_field(metadata: dict, version: str) -> list:
    version = get_metadata_version(metadata)
    if version == "OEMetadata-2.0":
        # Include resource index with each license for traceability
        licenses_per_resource = [
            (i, resource.get("licenses")) for i, resource in enumerate(metadata.get("resources", []))
        ]
    else:
        # Return -1 as a placeholder index for top-level licenses
        licenses_per_resource = [(0, metadata.get("licenses", []))]

    return licenses_per_resource


LICENSES = read_licenses()
