"""Tests for `inspection` module of OMI."""

import pathlib

from omi import inspection

CSV_DATA_FILE = pathlib.Path(__file__).parent / "test_data" / "inspection" / "data.csv"


def test_inspection():
    """Test inspection of test data file and check resulting metadata."""
    with CSV_DATA_FILE.open("r") as f:
        metadata = inspection.infer_metadata(f, "OEP")

    assert len(metadata["resources"]) == 1
    assert len(metadata["resources"][0]["schema"]["fields"]) == 9

    assert metadata["resources"][0]["schema"]["fields"][0]["name"] == "string"
    assert metadata["resources"][0]["schema"]["fields"][1]["name"] == "integer"
    assert metadata["resources"][0]["schema"]["fields"][2]["name"] == "number"
    assert metadata["resources"][0]["schema"]["fields"][3]["name"] == "array string"
    assert metadata["resources"][0]["schema"]["fields"][4]["name"] == "array integer"
    assert metadata["resources"][0]["schema"]["fields"][5]["name"] == "array float"
    assert metadata["resources"][0]["schema"]["fields"][6]["name"] == "object"
    assert metadata["resources"][0]["schema"]["fields"][7]["name"] == "date"
    assert metadata["resources"][0]["schema"]["fields"][8]["name"] == "bool"

    assert metadata["resources"][0]["schema"]["fields"][0]["type"] == "string"
    assert metadata["resources"][0]["schema"]["fields"][1]["type"] == "integer"
    assert metadata["resources"][0]["schema"]["fields"][2]["type"] == "float"
    assert metadata["resources"][0]["schema"]["fields"][3]["type"] == "array string"
    assert metadata["resources"][0]["schema"]["fields"][4]["type"] == "array integer"
    assert metadata["resources"][0]["schema"]["fields"][5]["type"] == "array float"
    assert metadata["resources"][0]["schema"]["fields"][6]["type"] == "object"
    assert metadata["resources"][0]["schema"]["fields"][7]["type"] == "date"
    assert metadata["resources"][0]["schema"]["fields"][8]["type"] == "boolean"


# TODO @jh-RLI: Add test for special cases in csv as e.g. this data will cause issues # noqa: TD003
# cat objective.csv
# ;0
# objective;97356714.15339188


COMMA_DATA_FILE = pathlib.Path(__file__).parent / "test_data" / "inspection" / "data_comma.csv"
TAB_DATA_FILE = pathlib.Path(__file__).parent / "test_data" / "inspection" / "data_tab.csv"


def test_detect_delimiter_semicolon():
    """Semicolon data holding commas inside JSON values must not be read as comma-separated."""
    assert inspection.detect_delimiter(CSV_DATA_FILE) == ";"


def test_detect_delimiter_comma():
    """Comma-separated data is detected as such."""
    assert inspection.detect_delimiter(COMMA_DATA_FILE) == ","


def test_detect_delimiter_tab():
    """Tab-separated data is detected as such."""
    assert inspection.detect_delimiter(TAB_DATA_FILE) == "\t"


def test_detect_delimiter_falls_back_on_unsamplable_source():
    """Sources that cannot be sampled fall back to the default delimiter."""
    assert inspection.detect_delimiter(object()) == inspection.DEFAULT_DELIMITER


def test_detect_delimiter_from_stream_keeps_stream_readable():
    """Sampling a stream rewinds it, so the caller can still read from the start."""
    with CSV_DATA_FILE.open("r") as f:
        assert inspection.detect_delimiter(f) == ";"
        assert f.readline().startswith("string;integer")


def test_inspection_comma_delimited():
    """Comma-separated data is split into columns instead of one merged field."""
    metadata = inspection.infer_metadata(str(COMMA_DATA_FILE), "OEP")
    fields = metadata["resources"][0]["schema"]["fields"]

    assert [field["name"] for field in fields] == ["name", "capacity", "region"]
    assert [field["type"] for field in fields] == ["string", "float", "string"]


def test_inspection_explicit_delimiter_overrides_detection():
    """An explicitly given delimiter is used instead of the detected one."""
    metadata = inspection.infer_metadata(str(COMMA_DATA_FILE), "OEP", delimiter=";")
    fields = metadata["resources"][0]["schema"]["fields"]

    assert len(fields) == 1
    assert fields[0]["name"] == "name,capacity,region"


def test_inspection_records_detected_dialect():
    """The delimiter actually used is recorded in the resource dialect."""
    metadata = inspection.infer_metadata(str(COMMA_DATA_FILE), "OEP")

    assert metadata["resources"][0]["dialect"]["delimiter"] == ","
    assert metadata["resources"][0]["dialect"]["decimalSeparator"] == "."


def test_inspection_fields_keep_documentation_slots():
    """Every field carries the spec's documentation keys, whatever its type."""
    with CSV_DATA_FILE.open("r") as f:
        metadata = inspection.infer_metadata(f, "OEP")

    for field in metadata["resources"][0]["schema"]["fields"]:
        assert set(field) == {"name", "description", "type", "nullable", "unit", "isAbout", "valueReference"}
