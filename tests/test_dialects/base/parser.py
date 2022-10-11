import datetime
import unittest

from omi.structure import Compilable
from omi.structure import Field
from omi.oem_structures import oem_v15


def _test_generic_parsing(parser, inp, expected, **kwargs):
    if parser:
        result = parser.parse_from_file(inp)
        assert_compileable_equal(expected, result, **kwargs)


def assert_compileable_equal(expected, got, nulls=None, exclude=None):
    exclude = exclude or []
    nulls = nulls or [None]
    assert isinstance(expected, (Compilable, dict)), type(expected)
    assert isinstance(got, (Compilable, dict)), (type(got), expected)
    for key in set(expected.__dict__.keys()).union(set(got.__dict__.keys())):
        if (
            key not in exclude
            and isinstance(getattr(expected, key), Field)
            or isinstance(getattr(expected, key), oem_v15.Field)
        ):
            l = getattr(expected, key)
            r = getattr(got, key)
            if isinstance(l, Compilable):
                new_exclude = []
                if isinstance(l, Field):
                    new_exclude = ["resource"]
                elif isinstance(l, oem_v15.Field):
                    new_exclude = ["resource"]
                assert_compileable_equal(l, r, nulls=nulls, exclude=new_exclude)
            elif isinstance(l, list) and isinstance(r, list):
                assert len(l) == len(
                    r
                ), "Lists do not match (Expected: {}; Got: {})".format(l, r)
                for l0, r0 in zip(sorted(l), sorted(r)):
                    if isinstance(l0, Compilable):
                        if isinstance(l0, Field):
                            new_exclude = ["resource"]
                        elif isinstance(l, oem_v15.Field):
                            new_exclude = ["resource"]
                        else:
                            new_exclude = []
                        assert_compileable_equal(
                            l0, r0, nulls=nulls, exclude=new_exclude
                        )
                    else:
                        assert l0 == r0, "Expected: {}; Got: {}".format(l0, r0)
            else:
                if not (l is None and r in nulls):
                    assert (
                        l == r
                    ), "Keys {} do not match (Expected:{}:{}; Got: {}:{})".format(
                        key, type(l), l, type(r), r
                    )


def parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%M-%d")
