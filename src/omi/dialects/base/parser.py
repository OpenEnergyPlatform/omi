from typing import TypeVar

from omi.structure import OEPMetadata

T = TypeVar("T")


class ParserException(Exception):
    pass


class Parser:
    """
    A parser is used to transform to read a specific metadata format and
    transform it into the internal metadata representation.
    """
    def parse(self, structure: T, *args, **kwargs) -> OEPMetadata:
        """
        Transforms the input structure into metadata as used by the
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

    def load_string(self, string: str, *args, **kwargs):
        """
        Load a string into the structure represented by the dialect
        Parameters
        ----------
        string: str

        Returns
        -------
            Translates the passed string into the format used as input for this parser
        """
        raise NotImplementedError

    def parse_from_string(
        self,
        string: str,
        load_args=None,
        parse_args=None,
        load_kwargs=None,
        parse_kwargs=None,
    ) -> OEPMetadata:
        """
        Parse a string into :class:`~omi.structure.OEPMetadata`

        Parameters
        ----------
        string

        Returns
        -------

        """
        return self.parse(
            self.load_string(string, *(load_args or []), **(load_kwargs or {})),
            *(parse_args or []),
            **(parse_kwargs or {})
        )

    @staticmethod
    def __unpack_file(file, **kwargs):
        """

        Parameters
        ----------

        Returns
        -------

        """
        with open(file, **kwargs, encoding='utf-8') as inp:
            return inp.read()

    def parse_from_file(self, file_path, *args, **kwargs):
        return self.parse_from_string(self.__unpack_file(file_path), *args, **kwargs)

    def is_valid(self, inp: str) -> bool:
        """
        Verify whether `inp` is a sting representation that is parsable by this
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

    def is_file_valid(self, file: str, **kwargs):
        """
        Verify whether the contents of the file under `file` is parsable by this
        parser

        Parameters
        ----------
        file: str
            Path to the file to validate

        **kwargs:

        Returns
        -------
        bool:
            Returns `True` iff the file's content is parsable

        """
        return self.is_valid(self.__unpack_file(file, **kwargs))
