# -*- coding: utf-8 -*-

from omi.dialects.rdf.parser import RDFParser

from ..base.parser import _test_generic_parsing
from ..internal_structures import metadata_v_1_4


def test_parser_rdf():
    parser = RDFParser()
    _input_file = "tests/data/metadata_v14.ttl"
    expected_result = metadata_v_1_4
    _test_generic_parsing(parser, _input_file, expected_result)
