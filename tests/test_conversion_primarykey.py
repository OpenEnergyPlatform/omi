"""
Regression tests: v1.5/v1.6 -> v2 primaryKey / foreignKeys coercion.

A v1.5 ``primaryKey`` stored as a comma-separated string (e.g. "id, scn_name")
must convert to a list of column names, not be iterated character by character.
A resource without foreign keys must yield ``foreignKeys: []``, not the v2
template placeholder stub.
"""

from __future__ import annotations

from omi.conversions.v160_to_v20 import (
    ___v2_populate_schema_foreign_keys as populate_fk,
)
from omi.conversions.v160_to_v20 import (
    ___v2_populate_schema_primary_keys as populate_pk,
)


def _resource_v2_template() -> dict:
    """Return a resource_v2 seeded with the v2 spec placeholders (as during conversion)."""
    return {
        "schema": {
            "primaryKey": [""],
            "foreignKeys": [{"fields": [""], "reference": {"resource": "", "fields": [""]}}],
        },
    }


def test_comma_separated_string_pk_splits_into_columns() -> None:
    """A comma-separated string primaryKey splits into one column per name."""
    rv2 = _resource_v2_template()
    populate_pk(rv2, {"schema": {"primaryKey": "id, scn_name"}})
    assert rv2["schema"]["primaryKey"] == ["id", "scn_name"]


def test_single_column_string_pk() -> None:
    """A single-column string primaryKey becomes a one-element list, not chars."""
    rv2 = _resource_v2_template()
    populate_pk(rv2, {"schema": {"primaryKey": "bus_id"}})
    assert rv2["schema"]["primaryKey"] == ["bus_id"]


def test_none_sentinel_pk_becomes_empty_list() -> None:
    """The v1.5 'none' sentinel maps to an empty primaryKey list."""
    rv2 = _resource_v2_template()
    populate_pk(rv2, {"schema": {"primaryKey": "none"}})
    assert rv2["schema"]["primaryKey"] == []


def test_list_pk_passes_through() -> None:
    """An already-list primaryKey is preserved unchanged."""
    rv2 = _resource_v2_template()
    populate_pk(rv2, {"schema": {"primaryKey": ["id", "scn_name"]}})
    assert rv2["schema"]["primaryKey"] == ["id", "scn_name"]


def test_missing_pk_becomes_empty_list() -> None:
    """A resource with no primaryKey yields an empty list."""
    rv2 = _resource_v2_template()
    populate_pk(rv2, {"schema": {}})
    assert rv2["schema"]["primaryKey"] == []


def test_empty_foreign_keys_yields_empty_list_not_stub() -> None:
    """An empty source foreignKeys list yields [], not the template stub."""
    rv2 = _resource_v2_template()
    populate_fk(rv2, {"schema": {"foreignKeys": []}})
    assert rv2["schema"]["foreignKeys"] == []


def test_absent_foreign_keys_yields_empty_list_not_stub() -> None:
    """A missing foreignKeys key yields [], not the template stub."""
    rv2 = _resource_v2_template()
    populate_fk(rv2, {"schema": {}})
    assert rv2["schema"]["foreignKeys"] == []


def test_populated_foreign_keys_are_carried_over() -> None:
    """A populated source foreignKey is carried into the v2 output."""
    rv2 = _resource_v2_template()
    populate_fk(
        rv2,
        {"schema": {"foreignKeys": [{"fields": ["bus_id"], "reference": {"resource": "grid.bus", "fields": ["id"]}}]}},
    )
    fks = rv2["schema"]["foreignKeys"]
    assert len(fks) == 1
    assert fks[0]["fields"] == ["bus_id"]
    assert fks[0]["reference"]["resource"] == "grid.bus"
