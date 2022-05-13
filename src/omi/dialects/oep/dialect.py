from omi.dialects.base.dialect import Dialect
from omi.dialects.base.register import register
from omi.dialects.oep.compiler import JSONCompiler
from omi.dialects.oep.compiler import JSONCompilerOEM15
from omi.dialects.oep.parser import JSONParser_1_3
from omi.dialects.oep.parser import JSONParser_1_4
from omi.dialects.oep.parser import JSONParser_1_5
from omi.dialects.oep.renderer import JSONRenderer
from omi.oem_structures import oem_v15


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


@register("oep-v1.5")
class OEP_V_1_5_Dialect(Dialect):
    _parser = JSONParser_1_5
    _compiler = JSONCompilerOEM15
    _renderer = JSONRenderer

    def compile(self, obj: oem_v15.OEPMetadata, *args, **kwargs):
        """
        Compiles the passed :class:`~omi.structure.OEPMetadata`-object into the
        structure fitting for this dialect

        Parameters
        ----------
        obj
            The :class:`~omi.structure.OEPMetadata`-object to compile

        Returns
        -------

        """
        c = self._compiler()
        return c.visit(obj, *args, **kwargs)

    def parse(self, string: str, *args, **kwargs) -> oem_v15.OEPMetadata:
        """
        Loads the passed string into an
        :class:`~omi.structure.OEPMetadata`-object.

        Parameters
        ----------
        string
            The string to parse

        Returns
        -------
            The :class:`~omi.structure.OEPMetadata`-object represented by `string`
        """
        p = self._parser()
        return p.parse_from_string(string, *args, **kwargs)

    def parse_file(self, path: str, *args, **kwargs) -> oem_v15.OEPMetadata:
        """
        Loads the passed string into an
        :class:`~omi.structure.OEPMetadata`-object.

        Parameters
        ----------
        string
            The string to parse

        Returns
        -------
            The :class:`~omi.structure.OEPMetadata`-object represented by `string`
        """
        p = self._parser()
        return p.parse_from_file(path, *args, **kwargs)

    def compile_and_render(self, obj: oem_v15.OEPMetadata, *args, **kwargs):
        """
        Combination of :func:`~omi.dialects.base.dialect.Dialect.compile` and :func:`~omi.dialects.base.dialect.Dialect.render`.
        """
        c = self._compiler()
        r = self._renderer()
        compiled = c.visit(obj, *args, **kwargs)
        return r.render(compiled, *args, **kwargs)
