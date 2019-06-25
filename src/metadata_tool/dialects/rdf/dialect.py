from metadata_tool.dialects.base.dialect import Dialect
from metadata_tool.dialects.base.register import register
from metadata_tool.dialects.rdf.compiler import RDFCompiler
from metadata_tool.dialects.rdf.parser import RDFParser
from metadata_tool.dialects.rdf.renderer import GraphRenderer
from metadata_tool.structure import OEPMetadata


@register("oep-rdf-v1.4")
class OEP_V_1_3_Dialect(Dialect):
    _parser = RDFParser
    _compiler = RDFCompiler
    _renderer = GraphRenderer

    def compile_and_render(self, obj: OEPMetadata, *args, **kwargs):
        c = self._compiler()
        r = self._renderer()
        c.visit(obj, *args, **kwargs)
        return r.render(c.graph, *args, **kwargs).decode("utf-8")
