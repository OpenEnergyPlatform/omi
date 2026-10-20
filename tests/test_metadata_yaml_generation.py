"""Tests for scaffolding the split-files YAML layout from an existing data folder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from omi.creation.init import init_dataset, init_resources_from_files

if TYPE_CHECKING:
    from pathlib import Path

ELEMENTS_CSV = "name;capacity;region\nwind1;12.5;DE\nwind2;8.0;FR\n"
COMMA_CSV = "name,value\na,1\nb,2\n"


def _write_datapackage(root: Path) -> list[Path]:
    """Create a minimal datapackage-style folder and return its data files."""
    elements = root / "data" / "elements"
    elements.mkdir(parents=True)
    semicolon = elements / "wind.csv"
    semicolon.write_text(ELEMENTS_CSV, encoding="utf-8")
    comma = elements / "comma_style.csv"
    comma.write_text(COMMA_CSV, encoding="utf-8")
    return [semicolon, comma]


def test_init_dataset_prefills_dataset_name(tmp_path: Path) -> None:
    """The dataset id lands in dataset.name instead of staying blank."""
    result = init_dataset(tmp_path / "metadata", "my_dp")

    doc = yaml.safe_load(result.dataset_yaml.read_text(encoding="utf-8"))
    assert doc["version"] == "OEMetadata-2.0"
    assert doc["dataset"]["name"] == "my_dp"


def test_init_resources_from_csv_folder(tmp_path: Path) -> None:
    """Resource stubs get name/path plus inferred schema for each CSV of a folder."""
    files = _write_datapackage(tmp_path / "my_dp")
    base_dir = tmp_path / "metadata"
    init_dataset(base_dir, "my_dp")

    outputs = init_resources_from_files(base_dir, "my_dp", files)

    assert {p.name for p in outputs} == {"wind.resource.yaml", "comma_style.resource.yaml"}

    wind = yaml.safe_load((base_dir / "resources" / "my_dp" / "wind.resource.yaml").read_text(encoding="utf-8"))
    assert wind["name"] == "wind"
    assert wind["path"].endswith("wind.csv")
    assert [field["name"] for field in wind["schema"]["fields"]] == ["name", "capacity", "region"]
    assert [field["type"] for field in wind["schema"]["fields"]] == ["string", "float", "string"]


def test_init_resources_fills_format_hints(tmp_path: Path) -> None:
    """Format hints are written even though the blank stub ships empty strings."""
    files = _write_datapackage(tmp_path / "my_dp")
    base_dir = tmp_path / "metadata"
    init_dataset(base_dir, "my_dp")
    init_resources_from_files(base_dir, "my_dp", files)

    wind = yaml.safe_load((base_dir / "resources" / "my_dp" / "wind.resource.yaml").read_text(encoding="utf-8"))
    assert wind["type"] == "table"
    assert wind["format"] == "CSV"
    assert wind["encoding"] == "UTF-8"
    assert wind["scheme"] == "file"
    assert wind["dialect"] == {"delimiter": ";", "decimalSeparator": "."}


def test_init_resources_detects_delimiter_per_file(tmp_path: Path) -> None:
    """A comma-separated CSV in the same folder is not merged into a single field."""
    files = _write_datapackage(tmp_path / "my_dp")
    base_dir = tmp_path / "metadata"
    init_dataset(base_dir, "my_dp")
    init_resources_from_files(base_dir, "my_dp", files)

    comma = yaml.safe_load(
        (base_dir / "resources" / "my_dp" / "comma_style.resource.yaml").read_text(encoding="utf-8"),
    )
    assert [field["name"] for field in comma["schema"]["fields"]] == ["name", "value"]
    assert comma["dialect"]["delimiter"] == ","


def test_init_resources_explicit_delimiter(tmp_path: Path) -> None:
    """An explicit delimiter is applied to all given files."""
    files = _write_datapackage(tmp_path / "my_dp")
    base_dir = tmp_path / "metadata"
    init_dataset(base_dir, "my_dp")
    init_resources_from_files(base_dir, "my_dp", files, delimiter=";")

    comma = yaml.safe_load(
        (base_dir / "resources" / "my_dp" / "comma_style.resource.yaml").read_text(encoding="utf-8"),
    )
    assert [field["name"] for field in comma["schema"]["fields"]] == ["name,value"]
