from omi.dialects.base.compiler import Compiler
from omi.dialects.base.parser import Parser
from omi.dialects.base.renderer import Renderer
from omi.structure import OEPMetadata


class Dialect:
    _parser = Parser
    _compiler = Compiler
    _renderer = Renderer

    def compile(self, obj: OEPMetadata, *args, **kwargs):
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

    def parse(self, string: str, *args, **kwargs) -> OEPMetadata:
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

    def render(self, structure, *args, **kwargs) -> str:
        """
        Turns the structure used by this dialect into a string

        Parameters
        ----------
        structure
            The structure to stringify

        Returns
        -------
            A string representation of `structure`
        """
        r = self._renderer()
        return r.render(structure, *args, **kwargs)

    def compile_and_render(self, obj: OEPMetadata, *args, **kwargs):
        """
        Combination of :func:`~omi.dialects.base.dialect.Dialect.compile` and :func:`~omi.dialects.base.dialect.Dialect.render`.
        """
        c = self._compiler()
        r = self._renderer()
        compiled = c.visit(obj, *args, **kwargs)
        return r.render(compiled, *args, **kwargs)
