"""Module to inspect data and create metadata from it."""

import csv
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, Union

from frictionless import Detector, Dialect, Resource
from frictionless.formats import CsvControl

from omi import base


class InspectionError(Exception):
    """Raised when an error occurs during inspection."""


#: Delimiters considered when guessing the dialect of a CSV file. The order is
#: also the tie-breaker, so the OEP convention (semicolon) wins a draw.
DELIMITER_CANDIDATES: tuple[str, ...] = (";", ",", "\t", "|")

#: Fallback used when no sample of the data can be read.
DEFAULT_DELIMITER = ";"

#: Number of lines read from the data to guess the delimiter.
_SAMPLE_LINES = 20


def _sample_from_path_or_text(data: Union[str, Path], max_lines: int) -> Optional[list[str]]:
    """Sample lines from a file path, or from inline CSV text if it is not a path."""
    path = Path(data)
    if not path.is_file():
        # Not a path but possibly inline CSV content
        return data.splitlines()[:max_lines] if isinstance(data, str) and "\n" in data else None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return [line for _, line in zip(range(max_lines), f)]
    except OSError:
        return None


def _sample_from_stream(data: Any, max_lines: int) -> Optional[list[str]]:  # noqa: ANN401
    """Sample lines from a seekable stream, rewinding it to its original position."""
    try:
        start = data.tell()
        lines = [line for _, line in zip(range(max_lines), data)]
        data.seek(start)
    except (OSError, ValueError):
        return None
    return [line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line for line in lines]


def _sample_lines(data: Any, max_lines: int = _SAMPLE_LINES) -> Optional[list[str]]:  # noqa: ANN401
    """
    Read up to `max_lines` lines from `data` without consuming it for later use.

    Accepts the same sources as :func:`infer_metadata`: a path (str/Path) or an
    open text stream. Streams are rewound afterwards, so the caller can still
    hand them to Frictionless.

    Returns
    -------
    Optional[list[str]]
        The sampled lines, or None if no sample could be taken (e.g. a
        non-seekable stream or an unsupported source type).
    """
    if isinstance(data, (str, Path)):
        return _sample_from_path_or_text(data, max_lines)
    if all(hasattr(data, attr) for attr in ("read", "seek", "tell")):
        return _sample_from_stream(data, max_lines)
    return None


def _column_counts(lines: list[str], delimiter: str) -> Optional[list[int]]:
    """
    Return the number of columns each line splits into, or None if unparsable.

    Returns
    -------
    Optional[list[int]]
        One column count per line, or None if `delimiter` cannot be used.
    """
    try:
        return [len(row) for row in csv.reader(lines, delimiter=delimiter)]
    except (csv.Error, TypeError):
        return None


def detect_delimiter(data: Any, candidates: tuple[str, ...] = DELIMITER_CANDIDATES) -> str:  # noqa: ANN401
    """
    Guess the column delimiter of tabular text data.

    A candidate is only accepted if it splits every sampled line into the same
    number of columns; among those, the candidate yielding the most columns
    wins. This keeps delimiters that merely occur *inside* quoted or
    JSON-shaped values (e.g. the commas in ``["a", "b"]``) from being mistaken
    for the real separator, which a plain occurrence count would fall for.

    Parameters
    ----------
    data: Any
        Data read from a CSV file or other source Frictionless may understand.
    candidates: tuple[str, ...]
        Delimiters to consider, in tie-breaking order.

    Returns
    -------
    str
        The detected delimiter, or :data:`DEFAULT_DELIMITER` if the data could
        not be sampled or no candidate fits.
    """
    lines = _sample_lines(data)
    if not lines:
        return DEFAULT_DELIMITER

    lines = [line for line in lines if line.strip()]
    if not lines:
        return DEFAULT_DELIMITER

    best: Optional[str] = None
    best_columns = 0
    for candidate in candidates:
        counts = _column_counts(lines, candidate)
        if not counts or len(set(counts)) != 1:
            # Inconsistent column count -> not the real delimiter.
            continue
        columns = counts[0]
        if columns > best_columns:
            best, best_columns = candidate, columns

    if best is None or best_columns < 2:  # noqa: PLR2004
        # Nothing splits the data consistently into more than one column.
        return DEFAULT_DELIMITER
    return best


def infer_metadata(data: Any, metadata_format: str, delimiter: Optional[str] = None) -> dict:  # noqa: ANN401
    """
    Guess metadata from data in given metadata format.

    Parameters
    ----------
    data: Any
        Data read from CSV file or other source frictionless may understand
    metadata_format: str
        Metadata format the inferred metadata should follow
    delimiter: Optional[str]
        Column delimiter of the data. If None (default), it is guessed with
        :func:`detect_delimiter`, falling back to
        :data:`DEFAULT_DELIMITER` when the data cannot be sampled.

    Returns
    -------
    dict
        OEMetadata guessed from data, containing name from CSV
    """
    latest_metadata_version = base.get_latest_metadata_version(metadata_format)
    template_metadata = base.get_metadata_specification(latest_metadata_version).template
    if template_metadata is None:
        raise InspectionError(f"No metadata template for metadata format {metadata_format} found.")

    if delimiter is None:
        delimiter = detect_delimiter(data)

    fields, resource = __guess_fields_from_data(data, delimiter)
    inferred_metadata = METADATA_TEMPLATE_ENGINE[metadata_format](template_metadata, fields, resource, delimiter)
    return inferred_metadata


def __guess_fields_from_data(data: Any, delimiter: str) -> tuple[list[dict[str, str]], Resource]:  # noqa: ANN401
    """
    Field names and types of data columns are detected by Frictionless.

    Parameters
    ----------
    data: Any
        Data read from CSV file or other source frictionless may understand
    delimiter: str
        Column delimiter of the data

    Returns
    -------
    list[dict[str, str]]
        List of fields holding name and type as strings
    Resource
        Extracted resource
    """
    csv_control = CsvControl(delimiter=delimiter)
    dialect = Dialect(controls=[csv_control])
    detector = Detector(field_float_numbers=True)
    resource = Resource(
        source=data,
        name="test",
        profile="tabular-data-resource",
        format="csv",
        dialect=dialect,
        detector=detector,
    )
    # Must be run, before schema can be inspected
    resource.infer()
    fields = resource.schema.to_dict()["fields"]
    return fields, resource


def __apply_fields_to_oep_metadata_template(
    metadata: dict,
    fields: list[dict[str, str]],
    resource: Resource,
    delimiter: str = DEFAULT_DELIMITER,
) -> dict:
    """
    Apply fields to metadata template for OEP metadata.

    Parameters
    ----------
    metadata: dict
        Metadata template
    fields: list[dict[str, str]]
        List of fields holding name and type as strings
    resource: Resource
        Extracted frictionless resource holding data
    delimiter: str
        Column delimiter of the data, written to the resource dialect

    Returns
    -------
    dict
        OEP metadata template holding guessed fields
    """
    type_mapping = {str(str): "string", str(int): "integer", str(float): "float"}

    def convert_field(field: dict[str, str]) -> dict[str, str]:
        """
        Convert frictionless field types to OEP types.

        This only includes conversion of number to float and detection of subtypes in arrays
        (currently, only string, integer and float are detected as subtypes).

        Parameters
        ----------
        field: dict[str, str]
            Frictionless field description

        Returns
        -------
        dict[str, str]
            Field description with OEP supported types
        """
        # Every field starts from the spec's field template, so that all
        # documentation slots (description, unit, isAbout, ...) are present for
        # the user to fill in - regardless of the detected type. Only name and
        # type are taken from Frictionless; its other field keys (floatNumber,
        # missingValues, ...) are not part of the OEMetadata field spec.
        oem_field = deepcopy(metadata["resources"][0]["schema"]["fields"][0])
        oem_field["name"] = field["name"]
        oem_field["type"] = field["type"]

        if field["type"] == "number":
            oem_field["type"] = "float"
        elif field["type"] == "array":
            # Detect the array subtype from the data (string, integer, float).
            oem_field["type"] = "array"
            for row in rows:
                if len(row[field["name"]]) == 0:
                    continue
                item_type = str(type(row[field["name"]][0]))
                oem_field["type"] = f"array {type_mapping[item_type]}"
                break
            # All arrays empty - no further subtype can be detected, keep "array"
        return oem_field

    rows = resource.read_rows()
    fields = [convert_field(field) for field in fields]

    metadata["resources"][0]["schema"]["fields"] = fields

    # Record the dialect actually used to read the data, so consumers do not
    # have to guess it again.
    dialect = metadata["resources"][0].get("dialect")
    if not isinstance(dialect, dict):
        dialect = {}
        metadata["resources"][0]["dialect"] = dialect
    dialect["delimiter"] = delimiter
    if not dialect.get("decimalSeparator"):
        # The spec template ships this as an empty string, so a plain
        # setdefault would leave it blank.
        dialect["decimalSeparator"] = "."
    return metadata


METADATA_TEMPLATE_ENGINE: dict[str, Callable] = {"OEP": __apply_fields_to_oep_metadata_template}

##########################################################################################
# Inspect form database tables using SQLAlchemy and return OEMetadata resource skeletons #
##########################################################################################


def inspect_db_table(engine_or_url: Union[str, object], schema_name: str, table_name: str) -> dict[str, Any]:
    """
    Inspect a database table using SQLAlchemy and return an OEMetadata resource dictionary skeleton.

    Parameters
    ----------
    engine_or_url: Union[str, sqlalchemy.engine.Engine]
        SQLAlchemy connection string or Engine instance.
    schema_name: str
        Name of the database schema.
    table_name: str
        Name of the database table.

    Returns
    -------
    dict
        A dictionary representing an OEMetadata resource skeleton with inferred fields.
    """
    try:
        import sqlalchemy.types as sqltypes
        from sqlalchemy import create_engine, inspect
    except ImportError as e:
        msg = "SQLAlchemy is required for database inspection. Please install it using `pip install sqlalchemy`."
        raise ImportError(
            msg,
        ) from e

    engine = create_engine(engine_or_url) if isinstance(engine_or_url, str) else engine_or_url

    inspector = inspect(engine)

    if not inspector.has_table(table_name, schema=schema_name):
        raise InspectionError(f"Table '{table_name}' not found in schema '{schema_name}'.")

    columns = inspector.get_columns(table_name, schema=schema_name)
    pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
    primary_keys = pk_constraint.get("constrained_columns", [])

    oem_fields = []
    for col in columns:
        col_type = col["type"]

        # TODO(jh-RLI): Mapping should be defined in a central place / OEM2ORM also defines mapping
        # https://github.com/OpenEnergyPlatform/omi/issues/147
        # Map SQLAlchemy types to frictionles/OEMetadata types
        if isinstance(col_type, sqltypes.Integer):
            oem_type = "integer"
        elif isinstance(col_type, (sqltypes.Numeric, sqltypes.Float)):
            oem_type = "number"
        elif isinstance(col_type, sqltypes.Boolean):
            oem_type = "boolean"
        elif isinstance(col_type, (sqltypes.Date, sqltypes.DateTime)):
            oem_type = "datetime"
        elif isinstance(col_type, sqltypes.ARRAY):
            oem_type = "array"
        # Check for GeoAlchemy2 Geometry types safely without importing geoalchemy2
        elif type(col_type).__name__ == "Geometry":
            oem_type = "geometry"
        else:
            oem_type = "string"

        oem_fields.append(
            {"name": col["name"], "description": "TODO: Add description", "type": oem_type, "unit": "none"},
        )

    resource_name = f"{schema_name}.{table_name}" if schema_name else table_name

    resource_skeleton = {
        "name": resource_name,
        "title": f"TODO: Add title for {resource_name}",
        "description": "TODO: Add description",
        "schema": {"primaryKey": primary_keys, "foreignKeys": [], "fields": oem_fields},
    }

    return resource_skeleton
