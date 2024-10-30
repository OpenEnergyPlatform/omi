"""Conversion module for OMI to update metadata to different versions."""

from __future__ import annotations

from copy import deepcopy

from omi.base import get_metadata_specification, get_metadata_version


class ConversionError(Exception):
    """Raised when a conversion fails."""


def convert_metadata(metadata: dict, target_version: str) -> dict:
    """
    Convert metadata to target version.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary
    target_version: str
        Target version to convert

    Returns
    -------
    dict
        Updated metadata
    """
    metadata_version = get_metadata_version(metadata)
    conversion_chain = __get_conversion_chain(metadata_version, target_version)
    converted_metadata = deepcopy(metadata)
    for next_version in conversion_chain[1:]:
        current_version = get_metadata_version(converted_metadata)
        converted_metadata = METADATA_CONVERSIONS[(current_version, next_version)](converted_metadata)
    return converted_metadata


def __get_conversion_chain(source_version: str, target_version: str) -> list[str]:
    """
    Try to find conversion chain from source version to target version.

    Parameters
    ----------
    source_version: str
        Starting version
    target_version: str
        Version goal

    Raises
    ------
    ConversionError
        if no conversion chain is found

    Returns
    -------
    list[str]
        List of conversion chain from source version to target version
    """

    def get_chain(current_version: str) -> list[str] | None:
        for source, target in METADATA_CONVERSIONS:
            if source != current_version:
                continue
            if target == target_version:
                # Solution found! Return last conversion tuple
                return [current_version, target_version]
            child_chain = get_chain(target)
            if child_chain is None:
                continue
            return [current_version, *child_chain]
        return None

    conversion_chain = get_chain(source_version)
    if conversion_chain:
        return conversion_chain
    raise ConversionError(f"No conversion chain found from {source_version} to {target_version}.")


def __convert_oep_152_to_160(metadata: dict) -> dict:
    """
    Convert metadata with version "OEP-1.5.2" to "OEP-1.6.0".

    Parameters
    ----------
    metadata: dict
        Metadata

    Returns
    -------
    dict
        Updated metadata
    """
    # No changes in metadata fields
    metadata["metaMetadata"]["metadataVersion"] = "OEP-1.6.0"
    return metadata


def __convert_oep_160_to_200(metadata: dict) -> dict:  # noqa: C901, PLR0915
    """
    Convert metadata with version "OEP-1.6.0" to "OEMetadata-2.0.0" using the v2.0 template.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary in v1.6 format

    Returns
    -------
    dict
        Updated metadata dictionary in v2.0 format
    """
    metadata_v2 = get_metadata_specification("OEMetadata-2.0.0")
    # Deep copy template to avoid mutating the original template
    metadata_v2 = deepcopy(metadata_v2.template)

    # Map v1.6 fields to v2.0 fields
    metadata_v2["name"] = None
    metadata_v2["title"] = None
    metadata_v2["id"] = None

    # Populate resources
    for i, resource in enumerate(metadata.get("resources", [])):
        if i >= len(metadata_v2["resources"]):
            metadata_v2["resources"].append(deepcopy(metadata_v2["resources"][0]))

        resource_v2 = metadata_v2["resources"][i]
        resource_v2["@id"] = metadata.get("@id")
        resource_v2["@context"] = metadata.get("@context")
        resource_v2["name"] = resource.get("name").split(".")[1]
        resource_v2["topics"] = [resource.get("name", "").split(".")[0]]
        resource_v2["title"] = metadata.get("title")
        resource_v2["path"] = metadata.get("id")
        resource_v2["description"] = metadata.get("description")
        resource_v2["languages"] = metadata.get("language", [])
        resource_v2["subject"] = metadata.get("subject", [])
        resource_v2["keywords"] = metadata.get("keywords", [])
        resource_v2["publicationDate"] = metadata.get("publicationDate")

        # Set to null to avoid validation errors: Date
        resource_v2["embargoPeriod"]["start"] = None
        resource_v2["embargoPeriod"]["end"] = None

        resource_v2["context"] = metadata.get("context", {})

        # Set to null to avoid validation errors: URI
        resource_v2["spatial"]["location"]["@id"] = None
        resource_v2["spatial"]["extent"]["name"] = metadata.get("spatial", {}).get("extent")
        # Set to null to avoid validation errors: URI
        resource_v2["spatial"]["extent"]["@id"] = None
        resource_v2["spatial"]["extent"]["resolutionValue"], resource_v2["spatial"]["extent"]["resolutionUnit"] = (
            metadata.get("spatial", {}).get("resolution", "").split(" ", 1)
        )

        resource_v2["temporal"] = metadata.get("temporal", {})
        # # Populate timeseries
        # for i_ts, timeseries in enumerate(metadata.get("temporal", {}).get("timeseries", [])):
        #     if i_ts >= len(resource_v2["temporal"]["timeseries"]):

        # Populate sources
        for i_source, source in enumerate(metadata.get("sources", [])):
            if i_source >= len(resource_v2["sources"]):
                resource_v2["sources"].append(deepcopy(metadata_v2["resources"][0]["sources"][0]))

            sources_v2 = resource_v2["sources"][i_source]
            sources_v2["title"] = source.get("title")
            sources_v2["description"] = source.get("description")
            sources_v2["path"] = source.get("path")
            for i_s_license, s_license in enumerate(source.get("licenses", [])):
                if i_s_license >= len(sources_v2["licenses"]):
                    resource_v2["sources"].append(deepcopy(metadata_v2["resources"][0]["sources"][0]["licenses"][0]))

                licenses_v2 = resource_v2["licenses"][i_s_license]
                licenses_v2.update(s_license)
                licenses_v2["copyrightStatement"] = None

        # _license to avoid shadowing python internal
        for i_license, _license in enumerate(metadata.get("licenses", [])):
            if i_license >= len(resource_v2["licenses"]):
                resource_v2["licenses"].append(deepcopy(metadata_v2["resources"][0]["licenses"][0]))

            licenses_v2 = resource_v2["licenses"][i_license]
            licenses_v2.update(_license)
            licenses_v2["copyrightStatement"] = None

        for i_contribution, contribution in enumerate(metadata.get("contributors", [])):
            if i_contribution >= len(resource_v2["contributors"]):
                resource_v2["contributors"].append(deepcopy(metadata_v2["resources"][0]["contributors"][0]))

            contributors_v2 = resource_v2["contributors"][i_contribution]
            contributors_v2["title"] = contribution.get("title")
            contributors_v2["path"] = contribution.get("path")
            contributors_v2["organization"] = contribution.get("organization")
            contributors_v2["date"] = contribution.get("date")
            contributors_v2["object"] = contribution.get("object")
            contributors_v2["comment"] = contribution.get("comment")

        # data resource/distribution definition
        resource_v2["type"] = None
        resource_v2["format"] = resource.get("format")
        resource_v2["encoding"] = resource.get("encoding")

        for i_s_field, field in enumerate(resource.get("schema", {}).get("fields", [])):
            if i_s_field >= len(resource_v2["schema"]["fields"]):
                resource_v2["schema"]["fields"].append(deepcopy(metadata_v2["resources"][0]["schema"]["fields"][0]))

            schema_fields_v2 = resource_v2["schema"]["fields"][i_s_field]
            schema_fields_v2["nullable"] = None
            schema_fields_v2.update(field)

        resource_v2["schema"]["primaryKey"] = resource.get("schema", {}).get("primaryKey", [])
        resource_v2["schema"]["foreignKeys"] = resource.get("schema", {}).get("foreignKeys", [])

        resource_v2["dialect"] = resource.get("dialect", {})
        resource_v2["review"] = metadata.get("review", {})

    # Update metaMetadata section
    metadata_v2["metaMetadata"]["metadataVersion"] = "OEMetadata-2.0.0"
    metadata_v2["metaMetadata"]["metadataLicense"] = metadata.get("metaMetadata", {}).get("metadataLicense")

    return metadata_v2


METADATA_CONVERSIONS = {
    ("OEP-1.5.2", "OEP-1.6.0"): __convert_oep_152_to_160,
    ("OEP-1.6.0", "OEMetadata-2.0.0"): __convert_oep_160_to_200,
}
