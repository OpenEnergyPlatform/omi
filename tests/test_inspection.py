"""Tests for `inspection` module of OMI."""

import pathlib

from omi import inspection

CSV_DATA_FILE = pathlib.Path(__file__).parent / "test_data" / "data.csv"


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
