"""Tests for the non-destructive DB merge-update wrapper in omi.creation.init."""

from __future__ import annotations

from omi.creation.init import update_resource_from_db_skeleton


def _resource() -> dict:
    """Return a resource with a human description and a soon-to-be-dropped column."""
    return {
        "name": "grid.t",
        "title": "Grid table",
        "description": "Human-written description.",
        "schema": {
            "primaryKey": ["id"],
            "fields": [
                {"name": "id", "description": "primary id", "type": "integer", "unit": "none"},
                {"name": "gone", "description": "was here", "type": "string", "unit": "none"},
            ],
        },
    }


def _db_skeleton() -> dict:
    """Return a DB skeleton with 'id' unchanged, a new 'extra', and 'gone' dropped."""
    return {
        "name": "grid.t",
        "schema": {
            "primaryKey": ["id"],
            "foreignKeys": [],
            "fields": [
                {"name": "id", "description": "TODO: Add description", "type": "integer", "unit": "none"},
                {"name": "extra", "description": "TODO: Add description", "type": "string", "unit": "none"},
            ],
        },
    }


def test_merge_preserves_human_description_and_adds_new_column() -> None:
    """Human descriptions survive; new DB columns arrive with a TODO placeholder."""
    updated, report = update_resource_from_db_skeleton(_resource(), _db_skeleton())
    fields = {f["name"]: f for f in updated["schema"]["fields"]}

    assert fields["id"]["description"] == "primary id"
    assert "extra" in fields
    assert "TODO" in fields["extra"]["description"]
    assert "gone" in fields
    assert report["missing_in_yaml"] == ["extra"]
    assert report["missing_in_db"] == ["gone"]


def test_merge_does_not_mutate_input() -> None:
    """The input resource is not mutated by the merge."""
    original = _resource()
    update_resource_from_db_skeleton(original, _db_skeleton())
    names = [f["name"] for f in original["schema"]["fields"]]
    assert names == ["id", "gone"]
