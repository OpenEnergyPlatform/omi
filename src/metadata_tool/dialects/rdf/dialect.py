from metadata_tool.dialects.base.dialect import Dialect
from metadata_tool.dialects.base.register import register
from metadata_tool.dialects.rdf.compiler import RDFCompiler
from metadata_tool.dialects.rdf.parser import RDFParser


@register("oep-rdf-v1.4")
class OEP_V_1_3_Dialect(Dialect):
    _parser = RDFParser
    _compiler = RDFCompiler
