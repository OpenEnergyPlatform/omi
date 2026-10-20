"""inspect_db_table reports the database's own column types and nullability."""

from __future__ import annotations

import pytest

from omi.inspection import inspect_db_table

sqlalchemy = pytest.importorskip("sqlalchemy")


def test_native_types_and_nullability() -> None:
    """Field types are DDL type names, not frictionless types; nullability is kept."""
    engine = sqlalchemy.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("CREATE TABLE t (id BIGINT PRIMARY KEY, name TEXT NOT NULL, share DOUBLE PRECISION)"),
        )
    resource = inspect_db_table(engine, "", "t")
    fields = {f["name"]: f for f in resource["schema"]["fields"]}
    assert fields["id"]["type"] == "bigint"
    assert fields["name"]["type"] == "text"
    assert fields["name"]["nullable"] is False
    assert fields["share"]["nullable"] is True
    assert resource["schema"]["primaryKey"] == ["id"]
