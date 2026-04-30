"""Module to inspect data and create metadata from it."""

from collections.abc import Callable
from copy import deepcopy
from typing import Any, Union

from frictionless import Detector, Dialect, Resource
from frictionless.formats import CsvControl

from omi import base


class InspectionError(Exception):
    """Raised when an error occurs during inspection."""


def infer_metadata(data: Any, metadata_format: str) -> dict:  # noqa: ANN401
    """
    Guess metadata from data in given metadata format.

    Note: It expects semicolon-delimited data.

    Parameters
    ----------
    data: Any
        Data read from CSV file or other source frictionless may understand
    metadata_format: str
        Metadata format the inferred metadata should follow

    Returns
    -------
    dict
        OEMetadata guessed from data, containing name from CSV
    """
    latest_metadata_version = base.get_latest_metadata_version(metadata_format)
    template_metadata = base.get_metadata_specification(latest_metadata_version).template
    if template_metadata is None:
        raise InspectionError(f"No metadata template for metadata format {metadata_format} found.")

    fields, resource = __guess_fields_from_data(data)
    inferred_metadata = METADATA_TEMPLATE_ENGINE[metadata_format](template_metadata, fields, resource)
    return inferred_metadata


def __guess_fields_from_data(data: Any) -> tuple[list[dict[str, str]], Resource]:  # noqa: ANN401
    """
    Field names and types of data columns are detected by Frictionless.

    Parameters
    ----------
    data: Any
        Data read from CSV file or other source frictionless may understand

    Returns
    -------
    list[dict[str, str]]
        List of fields holding name and type as strings
    Resource
        Extracted resource
    """
    csv_control = CsvControl(delimiter=";")
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


def __apply_fields_to_oep_metadata_template(metadata: dict, fields: list[dict[str, str]], resource: Resource) -> dict:
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
        if field["type"] == "number":
            return {"name": field["name"], "type": "float"}
        if field["type"] == "array":
            for row in rows:
                if len(row[field["name"]]) == 0:
                    continue
                item_type = str(type(row[field["name"]][0]))
                return {"name": field["name"], "type": f"array {type_mapping[item_type]}"}
            # All arrays are empty - so no further subtype can be detected
            return {"name": field["name"], "type": "array"}
        oem_field = deepcopy(metadata["resources"][0]["schema"]["fields"][0])
        oem_field.update(field)
        return oem_field

    rows = resource.read_rows()
    fields = [convert_field(field) for field in fields]

    metadata["resources"][0]["schema"]["fields"] = fields
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
