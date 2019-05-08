import unittest
import datetime

from collections import Iterable

from metadata_tool.structure import Compilable
class _TestParser(unittest.TestCase):

    __test__ = False

    _parser = None
    _input_file = None
    _expected_result = None

    def test_parsing(self):
        if self._parser:
            parser = self._parser()
            result = parser.parse_from_file(self._input_file)
            self.assertCompileableEqual(result, self._expected_result)


    def assertCompileableEqual(self, first, second):
        for key in first.__dict__.keys():
            l = getattr(first, key)
            r = getattr(second, key)
            if isinstance(l, Compilable):
                self.assertCompileableEqual(l,r)
            elif isinstance(l, Iterable) and isinstance(r, Iterable):
                for l0, r0 in zip(l, r):
                    if isinstance(l0, Compilable):
                        self.assertCompileableEqual(l0,r0)
                    else:
                        self.assertEqual(l0,r0)
            else:
                if l == 'none' and r is None:
                    return
                self.assertEqual(l,
                                 r,
                                 "Keys {} do not match".format(key))

def parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%M-%d")
