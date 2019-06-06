import datetime
import unittest

from metadata_tool.structure import Compilable, Field


def _test_generic_parsing(parser, inp, res, **kwargs):
    if parser:
        result = parser.parse_from_file(inp)
        assert_compileable_equal(result, res, **kwargs)


def assert_compileable_equal(first, second, nulls=frozenset(["none"]), exclude=None):
    exclude = exclude or []
    for key in (set(first.__dict__.keys()).union(set(second.__dict__.keys()))):
        if key not in exclude:
            l = getattr(first, key)
            r = getattr(second, key)
            if isinstance(l, Compilable):
                new_exclude = []
                if isinstance(l, Field):
                    new_exclude = ["resource"]
                print(key, new_exclude, type(l), first)
                assert_compileable_equal(l, r, nulls=nulls, exclude=new_exclude)
            elif isinstance(l, list) and isinstance(r, list):
                assert len(l) == len(r), "Lists do not match ({} != {})".format(l, r)
                for l0, r0 in zip(sorted(l), sorted(r)):
                    if isinstance(l0, Compilable):
                        if isinstance(l0, Field):
                            new_exclude = ["resource"]
                        else:
                            new_exclude = []
                        print(key, new_exclude, type(l0), first)
                        assert_compileable_equal(l0, r0, nulls=nulls, exclude=new_exclude)
                    else:
                        assert l0 == r0, "{} != {}".format(l0, r0)
            else:
                if l in nulls and r is None:
                    return

                assert l == r, "Keys {} do not match ({}:{} != {}:{})".format(key, type(l), l, type(r) ,r)


def parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%M-%d")
