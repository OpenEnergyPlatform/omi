from metadata_tool.dialects.oep.compiler import JSONCompiler
from ..internal_structures import metadata_v_1_4
import json


def test_compiler_v1_4():
    compiler = JSONCompiler()
    with open("tests/data/metadata_v14.json", "r") as _input_file:
        expected_result = json.load(_input_file)
        result = compiler.visit(metadata_v_1_4)
        assert_equal(expected_result, result)


def assert_equal(first, second, nulls=frozenset(["none"]), **kwargs):
    if isinstance(first, dict):
        assert_dict_equal(first, second, **kwargs)
    elif isinstance(first, list):
        assert_list_equal(first, second, **kwargs)
    else:
        if first in nulls and second is None:
            return
        assert first == second


def assert_dict_equal(first, second, **kwargs):
    for key in first.keys():
        if key not in second:
            raise Exception("Key \"{}\" missing in {}".format(key, second))
        assert_equal(first[key], second[key], **kwargs)


def assert_list_equal(first, second, **kwargs):
    assert len(first) == len(second), "Length mismatch ({}!={}) for {} and {}".format(
        len(first), len(second), first, second
    )

    for i, (l, r) in enumerate(zip(first, second)):
        try:
            assert_equal(l, r, **kwargs)
        except:
            print("Mismatch in element {}: {}!={}".format(i, l,r))
            raise
