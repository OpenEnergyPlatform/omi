"""Validation module for OMI."""

from __future__ import annotations

import warnings

import jsonschema
import pandas as pd
import requests
from frictionless import Field, Report, Resource, Schema
from frictionless.fields import (
    ArrayField,
    BooleanField,
    DateField,
    DatetimeField,
    IntegerField,
    NumberField,
    ObjectField,
    StringField,
)

from omi import license
from omi.base import (
    MetadataError,
    get_metadata_from_oep_table,
    get_metadata_specification,
    get_metadata_version,
)
from omi.settings import OEP_URL

FRICTIONLESS_FIELD_MAPPING = {
    "string": StringField,
    "text": StringField,
    "integer": IntegerField,
    "bigint": IntegerField,
    "float": NumberField,
    "float array": ArrayField,
    "double precision": NumberField,
    "boolean": BooleanField,
    "date": DateField,
    "datetime": DatetimeField,
    "array": ArrayField,
    "object": ObjectField,
    "json": ObjectField,
}


class ValidationError(Exception):
    """Exception raised when a validation fails."""


def validate_metadata(metadata: dict) -> None:
    """
    Validate metadata against related metadata schema.

    Parameters
    ----------
    metadata: dict
        Metadata

    Returns
    -------
    None
        if metadata schema is valid. Otherwise it raises an exception.
    """
    metadata_version = get_metadata_version(metadata)
    metadata_schema = get_metadata_specification(metadata_version)
    jsonschema.validate(metadata, metadata_schema.schema)
    license.validate_oemetadata_licenses(metadata)


def validate_data(
    data: pd.DataFrame,
    *,
    metadata: dict | None = None,
    oep_table: str | None = None,
    oep_schema: str | None = None,
    return_report: bool = False,
) -> None | Report:
    """
    Validate data against given metadata or table definition on OEP including metadata on OEP (if set).

    Parameters
    ----------
    data: pd.DataFrame
        Data to validate
    metadata: dict | None
        Metadata in OEMetadata format. If given, data is validated against metadata schema.
    oep_table: str | None
        Table name on OEP. If given, data is validated against OEP table.
    oep_schema: str | None
        Schema name on OEP. If given, data is validated against OEP table.
    return_report: bool
        If set to True, instead of raising an error if data is invalid an error report is returned

    Raises
    ------
    ValidationError
        if data is not in pandas.DataFrame format
        if field is missing in table or metadata definition
        if data does not fit to OEP table definition and/or metadata schema (if `return_report` is set to True,
        instead of raising an error a report is returned)

    Returns
    -------
    None
        if everything is valid. Otherwise, it raises an exception.
    """
    if not isinstance(data, pd.DataFrame):
        msg = "Data must be given as pandas.DataFrame."
        raise ValidationError(msg)
    if not metadata and (not oep_table or not oep_schema):
        msg = "You must either set metadata or OEP table to validate data against."
        raise ValidationError(msg)
    if metadata and (oep_table or oep_schema):
        msg = (
            "Cannot validate data against both metadata and OEP table. "
            "Please set only metadata or OEP table name and schema."
        )
        raise ValidationError(
            msg,
        )

    if metadata:
        return validate_data_against_metadata(data, metadata, return_report=return_report)
    return validate_data_against_oep_table(data, oep_table, oep_schema, return_report=return_report)


def validate_data_against_oep_table(
    data: pd.DataFrame,
    oep_table: str,
    oep_schema: str,
    *,
    return_report: bool = True,
) -> None | Report:
    """
    Validate data against given metadata.

    Parameters
    ----------
    data: pandas.DataFrame
        Data to validate
    oep_table: str
        OEP table name
    oep_schema: str
        OEP schema name
    return_report: bool
        If set to True, report is returned instead of raising an error.

    Returns
    -------
    Report
        Frictionless report if `return_report` is set to True, otherwise None is returned.
    """
    if not oep_table or not oep_schema:
        msg = "You must set OEP table AND schema."
        raise ValidationError(msg)

    # First validate data against table definition
    table_fields = __get_fields_from_oep_table(oep_table, oep_schema)
    report = __validate_data_against_schema(data, table_fields)
    if not report.valid:
        if return_report:
            return report
        raise ValidationError(f"Data validation failed against OEP table definition. Reason: {report.tasks[0].errors}")

    # Second, validate data against metadata from table
    try:
        metadata = get_metadata_from_oep_table(oep_table, oep_schema)
    except MetadataError:
        return None
    metadata_fields = __get_fields_from_metadata(metadata)
    report = __validate_data_against_schema(data, metadata_fields)
    if not report.valid:
        if return_report:
            return report
        raise ValidationError(
            f"Data validation failed against metadata from OEP table. Reason: {report.tasks[0].errors}",
        )
    return None


def validate_data_against_metadata(
    data: pd.DataFrame,
    metadata: dict,
    *,
    return_report: bool = True,
) -> None | Report:
    """
    Validate data against given metadata.

    Parameters
    ----------
    data: pandas.DataFrame
        Data to validate
    metadata: dict
        Metadata in OEMetadata format.
    return_report: bool
        If set to True, report is returned instead of raising an error.

    Returns
    -------
    Report
        Frictionless report if `return_report` is set to True, otherwise None is returned.
    """
    metadata_fields = __get_fields_from_metadata(metadata)
    report = __validate_data_against_schema(data, metadata_fields)
    if not report.valid:
        if return_report:
            return report
        raise ValidationError(f"Data validation failed. Reason: {report.tasks[0].errors}")
    return None


def validate_oep_table_against_metadata(  # noqa: C901
    oep_table: str,
    oep_schema: str,
    metadata: dict | None = None,
) -> None:
    """
    Validate OEP table against given metadata.

    Parameters
    ----------
    oep_table: str
        OEP table name
    oep_schema: str
        OEP schema name
    metadata: dict | None
        Metadata in OEMetadata format. If no metadata is given, metadata defined for OEP table on OEP is used.

    Raises
    ------
    ValidationError
        if OEP table schema does not fit metadata schema.

    Returns
    -------
    None
        if everything is valid. Otherwise, it raises an exception.
    """
    if metadata is None:
        metadata = get_metadata_from_oep_table(oep_table, oep_schema)

    # First check if metadata is even valid:
    validate_metadata(metadata)

    errors = []

    # Check resource name:
    if "resources" not in metadata:
        warnings.warn("No resource section defined in metadata. Cannot compare schema definitions.", stacklevel=1)
    if len(metadata["resources"]) > 1:
        warnings.warn(
            "Found more than one resource in metadata. Can only compare single resource with oep table definition.",
            stacklevel=1,
        )
    if "name" not in metadata["resources"][0]:
        raise ValidationError(
            f"Metadata resource has no name. It should be one of '{oep_table}', or '{oep_schema}.{oep_table}'.",
        )
    if (
        metadata["resources"][0]["name"] != oep_table
        and metadata["resources"][0]["name"] != f"{oep_schema}.{oep_table}"
    ):
        raise ValidationError(
            f"Name '{metadata['resources'][0]['name']}' of metadata resource does not fit to oep table name. "
            f"It should be one of '{oep_table}', or '{oep_schema}.{oep_table}'.",
        )

    # Compare fields and related types:
    oep_table_fields = __get_fields_from_oep_table(oep_table, oep_schema)
    metadata_fields = __get_fields_from_metadata(metadata)
    # Map fields to same field type format (using frictionless format as comparison format)
    mapped_oep_table_fields = {
        field.name: field.type for field in __map_fields_to_frictionless_fields(oep_table_fields)
    }
    mapped_metadata_fields = {field.name: field.type for field in __map_fields_to_frictionless_fields(metadata_fields)}
    for field_name, field_type in mapped_oep_table_fields.items():
        if field_name not in metadata_fields:
            errors.append(
                f"Field '{field_name}' from OEP table '{oep_schema}.{oep_table}' is missing in metadata schema.",
            )
            continue
        if field_type != mapped_metadata_fields[field_name]:
            errors.append(
                f"Field type '{oep_table_fields[field_name]}' from OEP table field '{field_name}' "
                f"differs from type '{metadata_fields[field_name]}' defined in metadata schema.",
            )
    for field_name in metadata_fields:
        if field_name not in oep_table_fields:
            errors.append(f"Field '{field_name}' not defined in OEP table '{oep_schema}.{oep_table}'.")  # noqa: PERF401
    if not errors:
        return
    raise ValidationError(errors)


def __validate_data_against_schema(data: pd.DataFrame, fields: dict[str, str]) -> Report:
    """
    Validate data against related schema definition and return frictionless report.

    Parameters
    ----------
    data: pandas.DataFrame
        Date to validate
    fields: dict[str, str]
        Dictionary of fields and their types to validate data with

    Returns
    -------
    Report
        Frictionless report of validated data
    """
    ordered_fields = {}
    for field in data.columns:
        if field not in fields:
            raise ValidationError(f"Could not find field '{field}' in schema.")
        ordered_fields[field] = fields[field]
    frictionless_fields = __map_fields_to_frictionless_fields(ordered_fields)
    schema = Schema(fields=frictionless_fields)
    resource = Resource(
        data=data,
        profile="tabular-data-resource",
        schema=schema,
    )
    report = resource.validate()
    return report


def __map_fields_to_frictionless_fields(fields: dict[str, str]) -> list[Field]:
    """
    Map fields to Frictionless fields.

    Parameters
    ----------
    fields: dict[str, str]
        Dictionary of fields holding name and related type as string

    Raises
    ------
    ValidationError
        if field cannot be mapped to Frictionless field

    Returns
    -------
    list[Field]
        List of frictionless Fields
    """
    frictionless_fields = []
    for field_name, field_type in fields.items():
        if field_type.endswith("[]"):
            # This indicates an array field
            frictionless_fields.append(ArrayField(name=field_name))
            continue
        if field_type not in FRICTIONLESS_FIELD_MAPPING:
            raise ValidationError(
                f"Field '{field_name} with type '{field_type}' cannot be mapped to Frictionless fields",
            )
        f_field = FRICTIONLESS_FIELD_MAPPING[field_type]
        frictionless_fields.append(f_field(name=field_name))
    return frictionless_fields


def __get_fields_from_oep_table(oep_table: str, oep_schema: str) -> dict[str, str]:
    """
    Get table fields and related types from OEP table.

    Parameters
    ----------
    oep_table: str
        Table name on OEP
    oep_schema: str
        Schema name on OEP

    Returns
    -------
    dict[str, str]
        Dictionary of table fields and related types.
    """
    response = requests.get(f"{OEP_URL}/api/v0/schema/{oep_schema}/tables/{oep_table}/columns", timeout=90)
    if response.status_code != requests.codes.ok:
        raise ValidationError(f"Could not find table '{oep_table}' in schema '{oep_schema}' on OEP.")
    table_fields = response.json()
    return {name: field["data_type"] for name, field in table_fields.items()}


def __get_fields_from_metadata(metadata: dict) -> dict[str, str]:
    """
    Get fields and related types from metadata.

    Parameters
    ----------
    metadata: dict
        Metadata in OEMetadata format.

    Raises
    ------
    ValidationError
        if fields cannot be extracted from metadata.

    Returns
    -------
    dict[str, str]
        Dictionary of fields and related types.
    """
    if "resources" not in metadata:
        msg = "No resources found in metadata."
        raise ValidationError(msg)
    if len(metadata["resources"]) > 1:
        msg = "More than one rsource found in metadata. Can only validate single resource."
        raise ValidationError(msg)
    if "schema" not in metadata["resources"][0]:
        msg = "No schema found in metadata resource."
        raise ValidationError(msg)
    if "fields" not in metadata["resources"][0]["schema"]:
        msg = "No fields found in resource schema."
        raise ValidationError(msg)
    return {field["name"]: field["type"] for field in metadata["resources"][0]["schema"]["fields"]}
