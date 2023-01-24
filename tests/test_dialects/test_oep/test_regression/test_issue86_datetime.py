import json
from unittest import SkipTest
from unittest import TestCase

from omi.dialects.oep import OEP_V_1_3_Dialect
from omi.dialects.oep import OEP_V_1_4_Dialect
from omi.dialects.oep import OEP_V_1_5_Dialect
from omi.dialects.oep.compiler import compile_date_or_none
from omi.dialects.oep.parser import ParserException
from omi.dialects.oep.parser import parse_date_or_none

# in the metadata, for some values we return the date,not the full datetime


class TestIssue86Datetime(TestCase):

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

    def roundtrip_value(self, value):
        value = parse_date_or_none(value)
        value = compile_date_or_none(value)
        return value

    def test_datetime_roundtrip(self):
        for bad_value in self.BAD_VALUES:
            self.assertRaises(ParserException, self.roundtrip_value, bad_value)
        for ok_value, exp_value in self.OK_VALUES.items():
            self.assertEqual(self.roundtrip_value(ok_value), exp_value)


class TestIssue86Metadata(TestIssue86Datetime):
    """test roundtrip in OEP_V_1_5_Dialect"""

    dialect = None
    OK_VALUES = {
        None: (None, None),
        2020: (2020, 2020),
        "2020": ("2020", "2020"),
        "2020-12": ("2020-12", "2020-12"),
        "2020-12-02": ("2020-12-02", "2020-12-02"),
        "2020-12-2": ("2020-12-02", "2020-12-02"),
        "2020-10-01T10:12:13": ("2020-10-01T10:12:13", "2020-10-01"),
        "2020-10-01 10:12": ("2020-10-01T10:12:00", "2020-10-01"),
        "2020-10-01T10:12:13+0200": ("2020-10-01T10:12:13+02:00", "2020-10-01"),
    }

    def test_datetime_roundtrip(self):
        # only actually run tests in subclasses
        if self.dialect:
            return super().test_datetime_roundtrip()

    def roundtrip_value(self, value):
        metadata_in = {"id": "test"}
        self.set_date_datetime_values(metadata_in, value)
        metadata_str = json.dumps(metadata_in)
        metadata_obj = self.dialect.parse(metadata_str)
        metadata_out = self.dialect.compile(metadata_obj)
        return self.get_date_datetime_values(metadata_out)

    def set_date_datetime_values(self, metadata, value):
        raise NotImplementedError()

    def get_date_datetime_values(self, metadata):
        raise NotImplementedError()


class TestIssue86Datetime_V_1_5(TestIssue86Metadata):
    """test roundtrip in OEP_V_1_5_Dialect"""

    dialect = OEP_V_1_5_Dialect()

    def set_date_datetime_values(self, metadata, value):
        metadata["publicationDate"] = value
        metadata["temporal"] = {"timeseries": [{"start": value}]}

    def get_date_datetime_values(self, metadata):
        v_datetime = metadata["temporal"]["timeseries"][0].get("start")
        v_date = metadata.get("publicationDate")
        return (v_datetime, v_date)


class TestIssue86Datetime_V_1_4(TestIssue86Metadata):
    """test roundtrip in OEP_V_1_4_Dialect"""

    dialect = OEP_V_1_4_Dialect()

    def set_date_datetime_values(self, metadata, value):
        metadata["publicationDate"] = value
        metadata["temporal"] = {"timeseries": {"start": value}}

    def get_date_datetime_values(self, metadata):
        v_datetime = metadata["temporal"]["timeseries"].get("start")
        v_date = metadata.get("publicationDate")
        return (v_datetime, v_date)
