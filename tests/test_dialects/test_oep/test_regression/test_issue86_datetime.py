import json
import re
from unittest import TestCase

from omi.dialects.oep import OEP_V_1_3_Dialect
from omi.dialects.oep import OEP_V_1_4_Dialect
from omi.dialects.oep import OEP_V_1_5_Dialect
from omi.dialects.oep.parser import ParserException
from omi.dialects.oep.parser import parse_date_or_none

BAD_VALUES = ["", "202", "2020-1", {}]
OK_VALUES = [
    None,
    1970,
    "1970",
    "2020-10",
    "2020-10-01",
    "2020-10-01 10:12",
    "2020-10-01T10:12:13",
    "2020-10-01T10:12:13:14+02:00",
    "2020-10-01T10:12:13-0200",
    "2020-10-01 10:12:13 GMT",
]

BAD_VALUES = []
OK_VALUES = []


class TestIssue86Datetime(TestCase):
    def datetime_roundtrip(self, value):
        """test function directly"""
        return parse_date_or_none(value)

    def test_datetime_roundtrip(self):
        for bad_value in BAD_VALUES:
            self.assertRaises(ParserException, self.datetime_roundtrip, bad_value)
        for ok_value in OK_VALUES:
            self.assertEqual(ok_value, self.datetime_roundtrip(ok_value), ok_value)


class TestIssue86Datetime_V_1_5(TestIssue86Datetime):
    """test roundtrip in OEP_V_1_5_Dialect"""

    def datetime_roundtrip(self, value):
        dialect = OEP_V_1_5_Dialect()
        metadata_in = {
            "id": "test",
            "temporal": {"timeseries": [{"start": value}]},
        }
        metadata_str = json.dumps(metadata_in)
        metadata_obj = dialect.parse(metadata_str)
        metadata_out = dialect.compile(metadata_obj)
        return metadata_out["temporal"]["timeseries"][0].get("start")
