from email import parser
import unittest
from omi.dialects.oep.parser import JSONParser_1_3
from omi.dialects.oep.parser import JSONParser_1_4
from omi.dialects.oep.parser import JSONParser_1_5

from ..base.parser import _test_generic_parsing
from ..internal_structures import metadata_v_1_3
from ..internal_structures import metadata_v_1_3_minimal
from ..internal_structures import metadata_v_1_4
from ..internal_structures import metadata_v_1_4_minimal
from ..internal_structures import metadata_v_1_5
from ..internal_structures import metadata_v_1_5_minimal
from omi.dialects.base.parser import ParserException

from metadata.latest.schema import OEMETADATA_LATEST_SCHEMA

import json


class ParserTest(unittest.TestCase):
    def test_parser_v1_3(self):
        parser = JSONParser_1_3()
        _input_file = "tests/data/metadata_v13.json"
        expected_result = metadata_v_1_3
        _test_generic_parsing(parser, _input_file, expected_result, nulls=["none", ""])

    def test_parser_v1_4(self):
        parser = JSONParser_1_4()
        _input_file = "tests/data/metadata_v14.json"
        expected_result = metadata_v_1_4
        _test_generic_parsing(parser, _input_file, expected_result)

    def test_parser_v1_4_Resource(self):
        parser = JSONParser_1_4()
        _input_file = "tests/data/metadata_v14_withoutresource.json"
        expected_result = metadata_v_1_4
        with self.assertRaises(ParserException):
            _test_generic_parsing(parser, _input_file, expected_result)

    def test_parser_v1_3_minimal(self):
        parser = JSONParser_1_3()
        _input_file = "tests/data/metadata_v13_minimal.json"
        expected_result = metadata_v_1_3_minimal
        _test_generic_parsing(parser, _input_file, expected_result)

    def test_parser_v1_4_minimal(self):
        parser = JSONParser_1_4()
        _input_file = "tests/data/metadata_v14_minimal.json"
        expected_result = metadata_v_1_4_minimal
        _test_generic_parsing(parser, _input_file, expected_result)

    def test_parser_v1_5(self):
        parser = JSONParser_1_5()
        _input_file = "tests/data/metadata_v15.json"
        expected_result = metadata_v_1_5
        _test_generic_parsing(parser, _input_file, expected_result)

    def test_parser_v1_5_is_valid(self):
        parser = JSONParser_1_5()
        _input_file = "tests/data/metadata_v15.json"

        with open(_input_file, "r", encoding="utf-8") as f:
            jsn = json.load(f)

        # file = parser.parse_from_file(_input_file)
        parser.validate(jsn)
