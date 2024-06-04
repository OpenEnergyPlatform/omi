"""Module to check licenses."""

import json
import re
from pathlib import Path

LICENCES_FILE = Path(__file__).parent / "data" / "licenses.json"


class LicenseError(Exception):
    """Exception raised when a license is invalid."""


def normalize_license_name(name: str) -> str:
    """
    Normalize license name.

    Replace whitespaces with hyphens and convert to uppercase

    Parameters
    ----------
    name: str
        License name

    Returns
    -------
    str
        Normalized license name
    """
    return re.sub(r"\s", "-", name).upper()


def read_licenses() -> set[str]:
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
    return {license_info.get("licenseId").upper() for license_info in licenses["licenses"]}


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
        if licences are valid, otherwise LicenseError is raised
    """
    if metadata is None:
        msg = "Metadata is empty."
        raise LicenseError(msg)

    licenses = metadata.get("licenses", [])

    if not licenses:
        msg = "No license information available in the metadata."
        raise LicenseError(msg)

    for i, license_ in enumerate(licenses):
        if not license_.get("name"):
            raise LicenseError(f"The license name is missing in {i}. license ({license_})")

        if not validate_license(license_["name"]):
            raise LicenseError(
                f"The (normalized) license name '{license_['name']}' was not found in the SPDX licenses list. "
                "(See https://github.com/spdx/license-list-data/blob/main/json/licenses.json).",
            )


LICENSES = read_licenses()
