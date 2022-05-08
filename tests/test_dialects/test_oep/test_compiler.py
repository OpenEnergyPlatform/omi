import json

from omi.dialects.oep.compiler import JSONCompiler, JSONCompilerOEM15

from ..internal_structures import metadata_v_1_4, metadata_v_1_5


def test_compiler_v1_5():
    compiler = JSONCompilerOEM15()
    with open("tests/data/metadata_v15.json", "r", encoding="utf-8") as _input_file:
        expected_result = json.load(_input_file)
        result = compiler.visit(metadata_v_1_5)
        assert_equal(expected_result, result)


def test_compiler_v1_4():
    compiler = JSONCompiler()
    with open("tests/data/metadata_v14.json", "r", encoding="utf-8") as _input_file:
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
    assert_list_equal(list(first.keys()), list(second.keys()), disregard_ordering=True)
    for key in first.keys():
        if key not in second:
            raise Exception('Key "{}" missing in {}'.format(key, second))
        assert_equal(first[key], second[key], **kwargs)


def assert_list_equal(first, second, disregard_ordering=False, **kwargs):
    assert len(first) == len(second), "Length mismatch ({}!={}) for {} and {}".format(
        len(first), len(second), first, second
    )

    if disregard_ordering:
        remaining = list(second)
        for expected in first:
            to_remove = None
            for i, result in enumerate(remaining):
                try:
                    assert_equal(
                        expected,
                        result,
                        disregard_ordering=disregard_ordering,
                        **kwargs
                    )
                except:
                    pass
                else:
                    to_remove = i
            if to_remove is not None:
                del remaining[to_remove]
            else:
                raise AssertionError(
                    "Element not found: {} in {}".format(expected, second)
                )
        if remaining:
            raise AssertionError(
                "Elements not found: {} in {}".format(remaining, first)
            )
    else:
        for i, (l, r) in enumerate(zip(first, second)):
            try:
                assert_equal(l, r, **kwargs)
            except:
                print("Mismatch in element {}: {}!={}".format(i, l, r))
                raise
