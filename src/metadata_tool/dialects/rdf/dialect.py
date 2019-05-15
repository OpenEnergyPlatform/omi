from metadata_tool.dialects.base.dialect import Dialect
from metadata_tool.dialects.base.register import register
from metadata_tool.dialects.rdf.compiler import RDFCompiler

@register("oep-rdf-v1.4")
class OEP_V_1_3_Dialect(Dialect):
    _parser = None
    _compiler = RDFCompiler
