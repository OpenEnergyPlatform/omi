"""Unit tests for omi.creation.coverage (store coverage reporting)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from omi.creation.coverage import (
    coverage_report,
    index_store_resources,
    resource_completeness,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------- resource_completeness ----------


def _complete_resource() -> dict:
    """Return a fully-documented resource dict for use as a test baseline."""
    return {
        "name": "grid.t",
        "title": "Grid table",
        "description": "A real description.",
        "schema": {"fields": [{"name": "id", "description": "primary id"}]},
    }


def test_completeness_complete_when_all_filled() -> None:
    """A fully-filled resource is classified complete with no reasons."""
    state, reasons = resource_completeness(_complete_resource())
    assert state == "complete"
    assert reasons == []


def test_completeness_skeleton_on_blank_required_field() -> None:
    """A blank required field makes the resource a skeleton."""
    res = _complete_resource()
    res["description"] = ""
    state, reasons = resource_completeness(res)
    assert state == "skeleton"
    assert any("description" in r for r in reasons)


def test_completeness_skeleton_on_placeholder() -> None:
    """A TODO placeholder in a required field makes the resource a skeleton."""
    res = _complete_resource()
    res["title"] = "TODO: Add title"
    state, _ = resource_completeness(res)
    assert state == "skeleton"


def test_completeness_skeleton_on_missing_field_description() -> None:
    """A schema field without a description makes the resource a skeleton."""
    res = _complete_resource()
    res["schema"]["fields"][0]["description"] = ""
    state, _ = resource_completeness(res)
    assert state == "skeleton"


def test_completeness_can_ignore_field_descriptions() -> None:
    """Field-description checks can be disabled via the flag."""
    res = _complete_resource()
    res["schema"]["fields"][0]["description"] = "TODO: Add description"
    state, _ = resource_completeness(res, require_field_descriptions=False)
    assert state == "complete"


# ---------- store indexing + coverage_report ----------


def _write_resource(base: Path, dataset_id: str, resource: dict) -> None:
    """Write a resource YAML plus a matching dataset stub under base."""
    safe = str(resource["name"]).replace(".", "_")
    d = base / "resources" / dataset_id
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{safe}.resource.yaml").write_text(yaml.safe_dump(resource), encoding="utf-8")
    ds = base / "datasets"
    ds.mkdir(parents=True, exist_ok=True)
    (ds / f"{dataset_id}.dataset.yaml").write_text(
        yaml.safe_dump({"version": "OEMetadata-2.0.4", "dataset": {"name": dataset_id}}),
        encoding="utf-8",
    )


def test_index_store_resources_maps_names(tmp_path: Path) -> None:
    """The store index maps each resource name to its YAML path."""
    _write_resource(tmp_path, "egon_grid", _complete_resource())
    index = index_store_resources(tmp_path)
    assert "grid.t" in index
    assert index["grid.t"].exists()


def test_coverage_report_classifies_missing_skeleton_complete_orphan(tmp_path: Path) -> None:
    """coverage_report sorts resources into complete/skeleton/missing/orphan."""
    _write_resource(tmp_path, "egon_grid", _complete_resource())
    skel = _complete_resource()
    skel["name"] = "grid.skel"
    skel["description"] = ""
    _write_resource(tmp_path, "egon_grid", skel)
    orphan = _complete_resource()
    orphan["name"] = "grid.orphan"
    _write_resource(tmp_path, "egon_grid", orphan)

    expected = ["grid.t", "grid.skel", "grid.absent"]
    report = coverage_report(tmp_path, expected)

    assert report.complete == ["grid.t"]
    assert [s.name for s in report.skeleton] == ["grid.skel"]
    assert report.missing == ["grid.absent"]
    assert "grid.orphan" in report.orphans
    assert report.ok is False


def test_coverage_report_ok_when_nothing_missing(tmp_path: Path) -> None:
    """coverage_report.ok is True when every expected resource exists."""
    _write_resource(tmp_path, "egon_grid", _complete_resource())
    report = coverage_report(tmp_path, ["grid.t"])
    assert report.ok is True
    assert report.summary().startswith("complete=1")
