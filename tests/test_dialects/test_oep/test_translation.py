import json
from collections import OrderedDict

from omi.dialects.oep.compiler import JSONCompiler
from omi.dialects.oep.parser import JSONParser_1_3

from .test_compiler import assert_equal


def test_translation_1_3_to_1_4():
    parser = JSONParser_1_3()
    compiler = JSONCompiler()
    with open("tests/data/metadata_v13_minimal.json", "r") as _input_file:
        input_string = _input_file.read()
        # Step 1: Parse JSON to internal structure
        internal_metadata = parser.parse_from_string(input_string)
        # Step 2: Translate to version 1_4
        result_json = compiler.visit(internal_metadata)

        expected_json = OrderedDict(json.loads('''{
    "metaMetadata": {
        "metadataVersion": "OEP-1.4.0",
        "metadataLicense": {
            "name": "CC0-1.0",
            "title": "Creative Commons Zero v1.0 Universal",
            "path": "https://creativecommons.org/publicdomain/zero/1.0/"}}}'''))

        assert_equal(expected_json, result_json)
