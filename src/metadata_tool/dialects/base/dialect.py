from metadata_tool.dialects.base.compiler import Compiler
from metadata_tool.dialects.base.parser import Parser
from metadata_tool.structure import OEPMetadata


class Dialect:
    _parser = Parser
    _compiler = Compiler

    def compile(self, obj:OEPMetadata, *args, **kwargs):
        c = self._compiler()
        return c.visit(obj, *args, ** kwargs)

    def parse(self, string: str, *args, **kwargs) -> OEPMetadata:
        p = self._parser()
        return p.parse(string, *args, **kwargs)

