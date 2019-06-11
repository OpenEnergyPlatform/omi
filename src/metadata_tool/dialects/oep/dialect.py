from metadata_tool.dialects.base.dialect import Dialect
from metadata_tool.dialects.base.register import register
from metadata_tool.dialects.oep.compiler import JSONCompiler
from metadata_tool.dialects.oep.parser import JSONParser_1_3
from metadata_tool.dialects.oep.parser import JSONParser_1_4
from metadata_tool.dialects.oep.renderer import JSONRenderer


@register("oep-v1.3")
class OEP_V_1_3_Dialect(Dialect):
    _parser = JSONParser_1_3
    _compiler = None
    _renderer = JSONRenderer


@register("oep-v1.4")
class OEP_V_1_4_Dialect(Dialect):
    _parser = JSONParser_1_4
    _compiler = JSONCompiler
    _renderer = JSONRenderer
