from typing import Callable, TypeVar, Any

from metadata_tool.structure import OEPMetadata

T = TypeVar("T")


class Parser:
    def parse(self, inp: str) -> OEPMetadata:
        """
        Transforms the input string into metadata as used by the
        OpenEnergyPlatform

        Parameters
        ----------
        inp: str
            The input string that should be parsed into OEP metadata

        Returns
        -------
        OEPMetadata
            OEP metadata represented by `inp`
        """
        raise NotImplementedError

    @staticmethod
    def __unpack_file(f: Callable[[Any, str, ...], [T]]):
        """

        Parameters
        ----------
        f

        Returns
        -------

        """

        def from_file(self, path: str, *args, file_kwargs=None, **kwargs) -> T:
            """

            Parameters
            ----------
            path: str
                Path of the file to call `f` on
            args
                Additional arguments to pass to `f`
            file_kwargs
                Additional parameters to pass to the `open` function
            kwargs
                Additional parameters to pass to `f`

            Returns
            -------

            """
            with open(path, **file_kwargs) as inp:
                return f(inp.read(), *args, **kwargs)

        return from_file

    parse_from_file = __unpack_file(parse)

    def is_valid(self, inp: str) -> bool:
        """
        Verify if `inp` is a sting representation that is parsable by this
        parser

        Parameters
        ----------
        inp: str
            String to verify

        Returns
        -------
        bool:
            Indicated whether this object is parsable or not

        """
        raise NotImplementedError

    is_file_valid = __unpack_file(is_valid)
