"""
Integration tests for OEMetadata assembly and entry point using real YAML.

This test suite consumes the example YAML tree located at:
tests/test_data/create/metadata/
and verifies that OMI assembles and writes a valid OEMetadata document.
"""

from __future__ import annotations

import json
from pathlib import Path

from omi.create import build_from_yaml
from omi.creation.assembler import assemble_metadata_dict


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
