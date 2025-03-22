"""Utility functions for data conversion."""

import re


def find_temporal_resolution_value_and_unit(resolution: str) -> tuple[str, str]:
    """
    Find temporal resolution value and unit from a resolution string.

    For temporal resolution, if the string starts with a number, this function will extract the number
    as the value and any following alphabetical characters as the unit. If no leading numeric value is found,
    the whole string is treated as a descriptive resolution with an empty unit.

    Possible formats:
      - "yearly"
      - "hourly"
      - "1 h"
      - "5 years"
      - "1h"

    Parameters
    ----------
    resolution: str
        Temporal resolution string.

    Returns
    -------
    tuple[str, str]
        Temporal resolution value and unit.
    """
    # Try matching a number (with optional decimals) and an optional unit, allowing for spaces in between.
    match = re.match(r"^\s*(\d+(?:\.\d+)?)(?:\s*([a-zA-Z]+))?\s*$", resolution)
    if match:
        value = match.group(1)
        unit = match.group(2) if match.group(2) is not None else ""
        return value, unit

    # If no numeric pattern is detected, return the entire trimmed string as the value.
    return resolution.strip(), ""


def find_spatial_resolution_value_and_unit(resolution: str) -> tuple[str, str]:
    """
    Find spatial resolution value and unit from a resolution string.

    For spatial resolution, this function attempts to extract a numeric value with a 'm' (meters) unit,
    as in "100 m" or even when embedded in a longer string like "vector, 10 m". If such a pattern is found,
    the numeric part is returned as the value and the unit is set to "m". Otherwise, the entire string
    is returned as a descriptive resolution (value) with an empty unit.

    Possible formats:
      - "vector, 10 m"
      - "100 m"
      - "Germany"
      - "NUTS-0"
      - "MVGD"
      - "Regionale Planungsgemeinschaften und Berlin"
      - "national"
      - "country"

    Parameters
    ----------
    resolution: str
        Spatial resolution string.

    Returns
    -------
    tuple[str, str]
        Spatial resolution value and unit (unit is expected to be 'm' when a numeric resolution is provided).
    """
    # Search for a numeric value followed by optional whitespace and an 'm' unit (case-insensitive).
    match = re.search(r"(\d+(?:\.\d+)?)\s*m\b", resolution, re.IGNORECASE)
    if match:
        value = match.group(1)
        unit = "m"
        return value, unit

    # If no numeric pattern is detected, return the entire trimmed string as the value.
    return resolution.strip(), ""


license_cc_by_4 = {
    "name": "CC-BY-4.0",
    "title": "Creative Commons Attribution 4.0 International",
    "path": "https://creativecommons.org/licenses/by/4.0/legalcode",
    "instruction": "You are free to share and adapt, but you must attribute and cant add additional restrictions. See https://creativecommons.org/licenses/by/4.0/deed.en for further information.",  # noqa: E501
    "attribution": "",
    "copyrightStatement": "",
}
