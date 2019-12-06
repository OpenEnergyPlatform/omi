from omi.dialects.base.dialect import Dialect
from omi.dialects.base.register import register
from omi.dialects.rdf.compiler import RDFCompiler
from omi.dialects.rdf.parser import RDFParser
from omi.dialects.rdf.renderer import GraphRenderer
from omi.structure import OEPMetadata


@register("oep-rdf-v1.4")
class OEP_V_1_4_RDF_Dialect(Dialect):
    _parser = RDFParser
    _compiler = RDFCompiler
    _renderer = GraphRenderer

    def compile_and_render(self, obj: OEPMetadata, *args, **kwargs):
        c = self._compiler()
        r = self._renderer()
        c.visit(obj, *args, **kwargs)
        return r.render(c.graph, *args, **kwargs).decode("utf-8")
