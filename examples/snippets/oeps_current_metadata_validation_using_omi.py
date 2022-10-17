from omi.dialects.oep.parser import ParserException
from omi.structure import Compilable

from omi.dialects.oep import OEP_V_1_4_Dialect, OEP_V_1_5_Dialect
from omi.dialects.oep.compiler import JSONCompiler

import json


# This is a list because I copied and pasted something and normally all oemeta data versions are checked - this is not relevant for you @Jann
METADATA_PARSERS = [OEP_V_1_5_Dialect()]
METADATA_COMPILERS = [OEP_V_1_5_Dialect(), JSONCompiler()]


# check 1 - is metadata parseable by OMI
def try_parse_metadata(inp):
    """

    Args:
        inp: string or dict or OEPMetadata

    Returns:
        Tuple[OEPMetadata or None, string or None]:
        The first component is the result of the parsing procedure or `None` if
        the parsing failed. The second component is None, if the parsing failed,
        otherwise an error message.

    Examples:

        >>> from api.actions import try_parse_metadata
        >>> result, error = try_parse_metadata('{"id":"id"}')
        >>> error is None
        True
 
    """

    if isinstance(inp, Compilable):
        # already parsed
        return inp, None
    elif not isinstance(inp, (str, bytes)):
        # in order to use the omi parsers, input needs to be str (or bytes)
        try:
            inp = json.dumps(inp)
        except Exception:
            return None, "Could not serialize json"

    last_err = None
    # try all the dialects
    for parser in METADATA_PARSERS:
        try:
            return parser.parse(inp), None
        except ParserException as e:
            return None, str(e)
        except Exception as e:
            last_err = e
            return None, str(e)
            # APIError(f"Metadata could not be parsed: {last_err}")
            # try next dialect

    print(f"Metadata could not be parsed: {last_err}")

# check 2 - Is metadata compilable by omi (complies with the oemetadata spec)
def try_compile_metadata(inp):
    """

    Args:
        inp: OEPMetadata - result of omi.parse(dict)

    Returns:
        Tuple[str or None, str or None]:
        The first component is the result of the compiling procedure or `None` if
        the compiling failed. The second component is None if the compiling failed,
        otherwise an error message.
    """
    last_err = None
    # try all the dialects
    for compiler in METADATA_COMPILERS:
        try:
            return compiler.compile(inp), None
        except Exception as e:
            last_err = e
            # APIError(f"Metadata could not be compiled: {last_err}")
            # try next dialect

    print(f"Metadata could not be compiled: {last_err}")

# use this instead of omis validation
# this is what is happening on the oep before the metadata is saved to persistence
def check_oemetadata_is_oep_compatible(_input_file = "examples/data/metadata_v15.json"):  

    with open(_input_file, "rb") as inp:
        # file = inp.read()
        metadata = json.load(inp)

    metadata_oep, err = try_parse_metadata(metadata)
    if not err:
        metadata_obj, err = try_compile_metadata(metadata_oep)
    else:
        raise Exception(err)

    if not err:
        metadata_str = json.dumps(metadata_obj, ensure_ascii=False)
        return metadata_str
    else:
        raise Exception(err)

