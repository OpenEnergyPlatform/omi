"""Regression test: the conversion contributor uses the v2 ``roles`` key and the conversion date."""

from __future__ import annotations

from datetime import datetime, timezone

from omi.conversions.v160_to_v20 import (
    ___v2_populate_contributors as populate_contributors,
)


def test_conversion_contributor_is_v2_conform() -> None:
    """The appended conversion contributor carries ``roles`` (not ``role``) and today's date."""
    resource_v2 = {"contributors": [{"title": ""}]}  # seeded from the v2 spec template, as in conversion
    populate_contributors(resource_v2, [{"title": "Jane Doe", "date": "2020-01-01"}])
    conversion = resource_v2["contributors"][-1]
    assert conversion["title"] == "Open Energy Platform oemetadata conversion to v2"
    assert conversion["roles"] == ["platform-maintainer"]
    assert "role" not in conversion
    assert conversion["date"] == datetime.now(tz=timezone.utc).date().isoformat()
