"""
Integration tests for OEMetadata assembly and entry point using YAML test data.

This test suite consumes the example YAML tree located at:
tests/test_data/create/metadata/
and verifies that OMI assembles and writes a valid OEMetadata document.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from omi.create import build_from_yaml
from omi.creation.assembler import assemble_metadata_dict

if TYPE_CHECKING:
    import pytest


def _fixture_metadata_root() -> Path:
    """Return the absolute path to tests/test_data/create/metadata."""
    here = Path(__file__).resolve().parent
    return here / "test_data" / "create" / "metadata"


def test_assemble_metadata_dict_with_fixture() -> None:
    """Assemble OEMetadata dict from the real fixture and assert key content."""
    base = _fixture_metadata_root()
    dataset_id = "powerplants"

    md = assemble_metadata_dict(base, dataset_id)

    # dataset-level checks (from powerplants.dataset.yaml)
    assert md["name"] == "oep_oemetadata"
    assert md["title"] == "OEP OEMetadata"
    assert md["@id"].startswith("https://databus.openenergyplatform.org/")

    # context injected from template if not overridden in resource
    assert "resources" in md
    assert isinstance(md["resources"], list)
    assert md["resources"]
    r_names = {r["name"] for r in md["resources"]}
    # Both resources from your example exist
    assert {"oemetadata_table", "data_2"}.issubset(r_names)

    # Check one resource that should have inherited from template
    r1 = next(r for r in md["resources"] if r["name"] == "oemetadata_table")
    assert r1["context"]["title"] == "NFDI4Energy"  # from template
    assert "licenses" in r1
    assert isinstance(r1["licenses"], list)
    assert r1["licenses"]
    assert r1["licenses"][0]["name"] in {"ODbL-1.0", "ODbL-1.0".upper(), "ODBL-1.0"}

    # Meta metadata is present
    assert "metaMetadata" in md
    assert md["metaMetadata"]["metadataVersion"].startswith("OEMetadata-2.0")


def test_entrypoint_build_from_yaml_writes_file(tmp_path: Path) -> None:
    """Use the real entry point to write JSON and compare basic structure."""
    base = _fixture_metadata_root()
    out = tmp_path / "out" / "powerplants.json"

    build_from_yaml(base, "powerplants", out)

    assert out.exists(), "Entry point did not write the output file."
    written = json.loads(out.read_text(encoding="utf-8"))

    # Sanity checks on written JSON
    assert written["name"] == "oep_oemetadata"
    assert isinstance(written["resources"], list)
    assert written["resources"]
    # Ensure unicode is preserved (© should not be escaped)
    licenses = written["resources"][0].get("licenses", [])
    if licenses:
        # stringify to inspect the character; ensure_ascii=False in writer preserves it
        text = json.dumps(licenses[0], ensure_ascii=False)
        assert "©" in text


def test_build_from_yaml_writes_file_when_output_is_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure build_from_yaml writes to the exact file path provided."""
    from omi import create as create_mod

    expected: dict[str, object] = {"name": "pp", "resources": []}

    # Avoid needing real YAML on disk
    def fake_assemble(
        _base_dir: Path,
        dataset_id: str,
        _index_file: Path | None = None,
    ) -> dict[str, object]:
        assert dataset_id == "powerplants"
        return expected

    monkeypatch.setattr(create_mod, "assemble_metadata_dict", fake_assemble)

    out = tmp_path / "out.json"
    create_mod.build_from_yaml(tmp_path / "meta", "powerplants", out)

    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8")) == expected


def test_build_many_from_yaml_writes_many_default_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure build_many_from_yaml writes <dataset_id>.json files into output_dir."""
    from omi import create as create_mod

    canned: dict[str, dict[str, object]] = {
        "a": {"name": "a", "resources": []},
        "b": {"name": "b", "resources": []},
    }

    def fake_many(
        _base_dir: Path,
        *,
        _dataset_ids: list[str] | None = None,
        _index_file: Path | None = None,
        as_dict: bool = True,
    ) -> dict[str, dict[str, object]]:
        # Called by build_many_from_yaml; return mapping id -> md
        assert as_dict is True
        return canned

    monkeypatch.setattr(create_mod, "assemble_many_metadata", fake_many)

    out_dir = tmp_path / "out"
    create_mod.build_many_from_yaml(tmp_path / "meta", out_dir)

    a_path = out_dir / "a.json"
    b_path = out_dir / "b.json"
    assert a_path.exists()
    assert b_path.exists()

    assert json.loads(a_path.read_text(encoding="utf-8")) == canned["a"]
    assert json.loads(b_path.read_text(encoding="utf-8")) == canned["b"]
