import json
from unittest import TestCase

from omi.dialects.oep import OEP_V_1_3_Dialect
from omi.dialects.oep import OEP_V_1_4_Dialect
from omi.dialects.oep import OEP_V_1_5_Dialect
from omi.dialects.oep.compiler import compile_date_or_none
from omi.dialects.oep.parser import ParserException
from omi.dialects.oep.parser import parse_date_or_none

BAD_VALUES = [True, {}, "", "not a date", "200", "2020-30-40", "2020-01-01 WTF"]
OK_VALUES = {
    None: None,
    2020: 2020,
    "2020": "2020",
    "2020-12": "2020-12",
    "2020-12-02": "2020-12-02",
    "2020-12-2": "2020-12-02",
    "2020-10-01T10:12:13": "2020-10-01T10:12:13",
    "2020-10-01 10:12": "2020-10-01T10:12:00",
    "2020-10-01T10:12:13+0200": "2020-10-01T10:12:13+02:00",
}


class TestIssue86Datetime(TestCase):
    def datetime_roundtrip(self, value):
        """test function directly"""
        value = parse_date_or_none(value)
        return compile_date_or_none(value)

    def test_datetime_roundtrip(self):
        for bad_value in BAD_VALUES:
            self.assertRaises(ParserException, self.datetime_roundtrip, bad_value)
        for ok_value, exp_value in OK_VALUES.items():
            self.assertEqual(self.datetime_roundtrip(ok_value), exp_value)
