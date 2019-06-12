# -*- coding: utf-8 -*-

from omi.dialects.oep.parser import JSONParser_1_3, JSONParser_1_4
from ..internal_structures import metadata_v_1_3, metadata_v_1_4
from ..base.parser import _test_generic_parsing


def test_parser_v1_3():
    parser = JSONParser_1_3()
    _input_file = "tests/data/metadata_v13.json"
    expected_result = metadata_v_1_3
    _test_generic_parsing(parser, _input_file, expected_result, nulls=["none", ""])


def test_parser_v1_4():
    parser = JSONParser_1_4()
    _input_file = "tests/data/metadata_v14.json"
    expected_result = metadata_v_1_4
    _test_generic_parsing(parser, _input_file, expected_result)


