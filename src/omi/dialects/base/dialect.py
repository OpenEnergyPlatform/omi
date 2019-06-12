from omi.dialects.base.compiler import Compiler
from omi.dialects.base.parser import Parser
from omi.dialects.base.renderer import Renderer
from omi.structure import OEPMetadata


class Dialect:
    _parser = Parser
    _compiler = Compiler
    _renderer = Renderer

    def compile(self, obj: OEPMetadata, *args, **kwargs):
        c = self._compiler()
        return c.visit(obj, *args, **kwargs)

    def parse(self, string: str, *args, **kwargs) -> OEPMetadata:
        p = self._parser()
        return p.parse(string, *args, **kwargs)

    def render(self, structure, *args, **kwargs) -> str:
        r = self._renderer()
        return r.render(structure, *args, **kwargs)

    def compile_and_render(self, obj: OEPMetadata, *args, **kwargs):
        c = self._compiler()
        r = self._renderer()
        compiled = c.visit(obj, *args, **kwargs)
        return r.render(compiled, *args, **kwargs)
