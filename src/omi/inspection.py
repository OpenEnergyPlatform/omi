"""Module to inspect data and create metadata from it."""

from typing import Any

from frictionless import Detector, Dialect, Resource
from frictionless.formats import CsvControl

from omi import base


class InspectionError(Exception):
    """Raised when an error occurs during inspection."""


def infer_metadata(data: Any, metadata_format: str) -> dict:  # noqa: ANN401
    """
    Guess metadata from data in given metadata format.

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

    fields = __guess_fields_from_data(data)
    inferred_metadata = METADATA_TEMPLATE_ENGINE[metadata_format](template_metadata, fields)
    return inferred_metadata


def __guess_fields_from_data(data: Any) -> list[dict[str, str]]:  # noqa: ANN401
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
    resource.read_rows()
    fields = resource.schema.to_dict()["fields"]
    return fields


def __apply_fields_to_oep_metadata_template(metadata: dict, fields: list[dict[str, Any]]) -> dict:
    metadata["resources"][0]["schema"]["fields"] = fields
    return metadata


METADATA_TEMPLATE_ENGINE = {"OEP": __apply_fields_to_oep_metadata_template}
