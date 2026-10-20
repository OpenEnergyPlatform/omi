"""Unit tests for omi.creation.sources (provenance source helpers)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from omi.creation.sources import (
    add_source_to_resource,
    add_source_to_resource_file,
    build_external_source,
    build_internal_source,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------- constructors ----------


def test_build_external_source_has_spec_keys_and_title() -> None:
    """An external source keeps title/description/path and stub spec keys."""
    src = build_external_source("MaStR", description="Registry", path="https://mastr.de")
    assert src["title"] == "MaStR"
    assert src["description"] == "Registry"
    assert src["path"] == "https://mastr.de"
    assert src["authors"] == []
    assert src["publicationYear"] is None
    assert src["sourceLicenses"] == []


def test_build_internal_source_references_table() -> None:
    """An internal source references the table and uses only spec keys."""
    src = build_internal_source("grid.egon_etrago_bus")
    assert "grid.egon_etrago_bus" in src["title"]
    assert "grid.egon_etrago_bus" in src["description"]
    assert set(src) == {"title", "description", "path", "authors", "publicationYear", "sourceLicenses"}


# ---------- add_source_to_resource ----------


def test_add_source_appends_and_does_not_mutate_input() -> None:
    """Adding a source returns a copy and leaves the input untouched."""
    resource = {"name": "grid.t", "sources": []}
    src = build_external_source("OSM", path="https://osm.org")
    updated, added = add_source_to_resource(resource, src)
    assert added is True
    assert len(updated["sources"]) == 1
    assert resource["sources"] == []


def test_add_source_creates_sources_list_when_absent() -> None:
    """A missing 'sources' key is created on first add."""
    resource = {"name": "grid.t"}
    updated, added = add_source_to_resource(resource, build_external_source("X"))
    assert added is True
    assert isinstance(updated["sources"], list)
    assert updated["sources"][0]["title"] == "X"


def test_add_source_dedupes_on_title_and_path() -> None:
    """An equivalent source (same title+path) is not added twice."""
    src = build_external_source("MaStR", path="https://mastr.de")
    resource = {"name": "grid.t", "sources": [src]}
    updated, added = add_source_to_resource(resource, build_external_source("MaStR", path="https://mastr.de"))
    assert added is False
    assert len(updated["sources"]) == 1


def test_add_source_same_title_different_path_is_new() -> None:
    """Same title but different path counts as a distinct source."""
    resource = {"name": "grid.t", "sources": [build_external_source("MaStR", path="a")]}
    updated, added = add_source_to_resource(resource, build_external_source("MaStR", path="b"))
    assert added is True
    assert len(updated["sources"]) == 2


# ---------- add_source_to_resource_file ----------


def test_add_source_to_file_writes_and_is_idempotent(tmp_path: Path) -> None:
    """Writing a source to a file persists once and is a no-op on repeat."""
    res_path = tmp_path / "grid_t.resource.yaml"
    res_path.write_text(yaml.safe_dump({"name": "grid.t", "sources": []}), encoding="utf-8")

    src = build_internal_source("grid.egon_etrago_bus")
    assert add_source_to_resource_file(res_path, src) is True

    reloaded = yaml.safe_load(res_path.read_text(encoding="utf-8"))
    assert len(reloaded["sources"]) == 1

    assert add_source_to_resource_file(res_path, src) is False
    reloaded = yaml.safe_load(res_path.read_text(encoding="utf-8"))
    assert len(reloaded["sources"]) == 1
