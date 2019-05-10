from typing import Any
from typing import Callable
from typing import TypeVar

from metadata_tool.structure import OEPMetadata

T = TypeVar("T")


class Parser:
    def parse(self, inp: str, *args, **kwargs) -> OEPMetadata:
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
    def __unpack_file(*args, **kwargs):
        """

        Parameters
        ----------

        Returns
        -------

        """
        with open(*args, **kwargs) as inp:
            return inp.read()

    def parse_from_file(self, file_path, *args, **kwargs):
        return self.parse(self.__unpack_file(file_path), *args, **kwargs)

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

    def is_file_valid(self, *args, **kwargs):
        return self.is_valid(self.__unpack_file(*args, **kwargs))
