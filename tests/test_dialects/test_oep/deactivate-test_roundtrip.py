import json
from itertools import combinations, product

from omi.dialects.oep.compiler import JSONCompiler
from omi.dialects.oep.parser import JSONParser_1_4
from omi.dialects.rdf.compiler import RDFCompiler
from omi.dialects.rdf.parser import RDFParser

from .test_compiler import assert_equal


def test_roundtrip():
    with open("tests/data/metadata_v14.json", "r") as _input_file:
        input_string = _input_file.read()
        assert_roundtrip(json.loads(input_string), input_string)


def assert_roundtrip(expected_json, input_string):
    json_compiler = JSONCompiler()
    json_parser = JSONParser_1_4()
    rdf_compiler = RDFCompiler()
    rdf_p = RDFParser()
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


def __mask(jsn, keep):
    if isinstance(jsn, dict):
        return [dict(zip(keys, items))
                for keys in combinations(jsn.keys(),2)
                for items in product(*(__mask(jsn[field], keep)
                                       if field not in keep else [jsn[field]]
                                       for field in keys))
                if keys and all(k not in jsn.keys() or k in keys for k in keep) ]
    if isinstance(jsn, list):
        if jsn:
            return [[possibility] + jsn[1:] for possibility in __mask(jsn[0], keep)]
        else:
            return [[]]
    else:
        return [jsn]


def test_roundtrip_with_missing_fields():
    json_compiler = JSONCompiler()
    json_parser = JSONParser_1_4()
    with open("tests/data/metadata_v14.json", "r") as _input_file:
        input_string = _input_file.read()
        for expected_json in __mask(json.loads(input_string), keep=["id", "metaMetadata"]):
            assert_equal(json_compiler.visit(json_parser.parse(expected_json)), expected_json)

