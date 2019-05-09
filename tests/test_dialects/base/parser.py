import unittest
import datetime

from metadata_tool.structure import Compilable


def _test_generic_parsing(parser, inp, res):
    if parser:
        result = parser.parse_from_file(inp)
        assertCompileableEqual(result, res)


def assertCompileableEqual(first, second):
    for key in (set(first.__dict__.keys()).union(set(second.__dict__.keys()))):
        l = getattr(first, key)
        r = getattr(second, key)
        if isinstance(l, Compilable):
            assertCompileableEqual(l, r)
        elif isinstance(l, list) and isinstance(r, list):
            assert len(l) == len(r), "Lists do not match ({} != {})".format(l, r)
            for l0, r0 in zip(l, r):
                if isinstance(l0, Compilable):
                    assertCompileableEqual(l0, r0)
                else:
                    assert l0 == r0, "{} != {}".format(l0, r0)
        else:
            if l == "none" and r is None:
                return
            assert l == r, "Keys {} do not match ({} != {})".format(key, l, r)


def parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%M-%d")
