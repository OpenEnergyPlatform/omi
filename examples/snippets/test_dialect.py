from omi.dialects.oep.dialect import OEP_V_1_3_Dialect, OEP_V_1_4_Dialect, OEP_V_1_5_Dialect
from omi.dialects.oep.parser import JSONParser
from omi.dialects.oep.parser import ParserException
from omi.structure import Compilable

from metadata.latest.schema import OEMETADATA_LATEST_SCHEMA

import json


def parse_and_compile():
    inp = '{"id":"unique_id"}' #or read from json file
    dialect1_5 = OEP_V_1_5_Dialect()
    parsed = dialect1_5.parse(inp)
    print(parsed)
    parsed.identifier = "anotehr_unique_id"
    compiled = dialect1_5.compile(parsed)
    print(compiled)

def validate_oemetadata():
    parser = JSONParser()
    _input_file = "0_local_test/metadata_v15.json"

    # parser = JSONParser_1_5()
    # _input_file = "tests/data/metadata_v15.json"

    with open(_input_file, "rb") as inp:
        # file = inp.read()
        file = json.load(inp)

    # file = parser.parse_from_file(_input_file)
    # parser.validate(file, [OEMETADATA_LATEST_SCHEMA])
    return parser.is_valid(file)


# validate_oemetadata()

from omi.dialects.oep import OEP_V_1_4_Dialect, OEP_V_1_5_Dialect
from omi.dialects.oep.compiler import JSONCompiler

import pathlib

METADATA_PARSERS = [OEP_V_1_5_Dialect(), OEP_V_1_4_Dialect()]
METADATA_COMPILERS = [OEP_V_1_5_Dialect(),  OEP_V_1_4_Dialect(), JSONCompiler()]

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


def try_compile_metadata(inp):
    """

    Args:
        inp: OEPMetadata

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


def set_table_metadata(metadata):
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


def save_json(data: json, save_at: pathlib.Path = "examples/data/output/", filename: str = "omi_processed_metadata.json"):

    pathlib.Path(save_at).mkdir(parents=True, exist_ok=True)
    with open(f"{save_at}{filename}", "w", encoding="utf-8") as fp:
        fp.write(data)


def run_oep_case():
    # _input_file = "tests/data/metadata_v15.json"
    _input_file = "examples/data/metadata_v15.json"

    with open(_input_file, "rb") as inp:
        # file = inp.read()
        file = json.load(inp)

    jsn = set_table_metadata(file)

    save_json(data = jsn)

run_oep_case()