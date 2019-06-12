import json

from omi.dialects.oep.compiler import JSONCompiler
from omi.dialects.oep.parser import JSONParser_1_4
from omi.dialects.rdf.compiler import RDFCompiler
from omi.dialects.rdf.parser import RDFParser
from .test_compiler import assert_equal


def test_roundtrip():
    json_compiler = JSONCompiler()
    json_parser = JSONParser_1_4()
    rdf_compiler = RDFCompiler()
    rdf_p = RDFParser()
    with open("tests/data/metadata_v14.json", "r") as _input_file:
        input_string = _input_file.read()
        expected_json = json.loads(input_string)
        # Step 1: Parse JSON to internal structure
        internal_metadata = json_parser.parse_from_string(input_string)
        # Step 2: Translate to rdf
        _ = rdf_compiler.visit(internal_metadata)
        # Step 3: Parse rdf string
        internal_metadata2 = rdf_p.parse(rdf_compiler.graph)
        # Step 4: Translate to JSON
        result_json = json_compiler.visit(internal_metadata2)
        # Final step: Compare
        assert_equal(expected_json, result_json, disregard_ordering=True)
