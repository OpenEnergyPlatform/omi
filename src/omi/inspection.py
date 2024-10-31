"""Module to inspect data and create metadata from it."""

from collections.abc import Callable
from typing import Any

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
        return field

    rows = resource.read_rows()
    fields = [convert_field(field) for field in fields]

    metadata["resources"][0]["schema"]["fields"] = fields
    return metadata


METADATA_TEMPLATE_ENGINE: dict[str, Callable] = {"OEP": __apply_fields_to_oep_metadata_template}
