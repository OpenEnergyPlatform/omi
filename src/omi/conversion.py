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


def __convert_oep_160_to_201(metadata: dict) -> dict:
    """
    Convert metadata with version "OEP-1.6.0" to "OEMetadata-2.0.1" using the v2.0 template.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary in v1.6 format

    Returns
    -------
    dict
        Updated metadata dictionary in v2.0 format
    """
    metadata_v2 = deepcopy(get_metadata_specification("OEMetadata-2.0.1").template)
    metadata_v2["name"] = metadata_v2["title"] = metadata_v2["id"] = metadata_v2["description"] = None

    # Populate metadata v2 resources
    for i, resource in enumerate(metadata.get("resources", [])):
        resource_v2 = ___v2_ensure_resource_entry(metadata_v2, i)
        ___v2_populate_resource_v2(resource_v2, metadata, resource)

    # Update metaMetadata section
    metadata_v2["metaMetadata"]["metadataVersion"] = "OEMetadata-2.0.1"
    metadata_v2["metaMetadata"]["metadataLicense"] = metadata.get("metaMetadata", {}).get("metadataLicense")

    return metadata_v2


def ___v2_ensure_resource_entry(metadata_v2: dict, index: int) -> dict:
    """Ensure a resource entry exists in metadata_v2 resources for the given index."""
    if index >= len(metadata_v2["resources"]):
        metadata_v2["resources"].append(deepcopy(metadata_v2["resources"][0]))
    return metadata_v2["resources"][index]


def ___v2_populate_resource_v2(resource_v2: dict, metadata: dict, resource: dict) -> None:
    """Populate resource_v2 fields based on metadata and resource from v1.6."""
    # Bulk update keys without
    resource_v2.update(
        {
            "@id": metadata.get("@id"),
            "@context": metadata.get("@context"),
            "name": resource.get("name").split(".")[1],
            "topics": [resource.get("name", "").split(".")[0]],
            "title": metadata.get("title"),
            "path": metadata.get("id"),
            "description": metadata.get("description"),
            "languages": metadata.get("language", []),
            "subject": metadata.get("subject", []),
            "keywords": metadata.get("keywords", []),
            "publicationDate": metadata.get("publicationDate"),
            "context": metadata.get("context", {}),
            "temporal": metadata.get("temporal", {}),
            "type": None,
            "format": resource.get("format"),
            "encoding": resource.get("encoding"),
            "schema": {
                "fields": resource.get("schema", {}).get("fields", []),
                "primaryKey": resource.get("schema", {}).get("primaryKey", []),
                "foreignKeys": resource.get("schema", {}).get("foreignKeys", []),
            },
            "dialect": resource.get("dialect", {}),
            "review": metadata.get("review", {}),
        },
    )

    resource_v2["context"]["publisher"] = None

    resource_v2["embargoPeriod"]["start"] = None
    resource_v2["embargoPeriod"]["end"] = None

    # Set to null to avoid validation errors: URI
    resource_v2["spatial"]["location"]["@id"] = None
    resource_v2["spatial"]["location"]["address"] = metadata.get("spatial", {}).get("location")
    resource_v2["spatial"]["location"]["latitude"] = None
    resource_v2["spatial"]["location"]["longitude"] = None
    # Set to null to avoid validation errors: URI
    resource_v2["spatial"]["extent"]["name"] = metadata.get("spatial", {}).get("extent")
    resource_v2["spatial"]["extent"]["@id"] = None
    resource_v2["spatial"]["extent"]["resolutionValue"], resource_v2["spatial"]["extent"]["resolutionUnit"] = (
        metadata.get("spatial", {}).get("resolution", "").split(" ", 1)
    )
    resource_v2["spatial"]["extent"]["crs"] = None

    ___v2_populate_sources(resource_v2, metadata.get("sources", []))
    ___v2_populate_contributors(resource_v2, metadata.get("contributors", []))
    ___v2_populate_licenses(resource_v2, metadata.get("licenses", []))
    ___v2_populate_schema_fields(resource_v2, resource)


def ___v2_populate_sources(resource_v2: dict, sources: list) -> None:
    """Populate sources in resource_v2 from sources in v1.6."""
    for i_source, source in enumerate(sources):
        if i_source >= len(resource_v2["sources"]):
            resource_v2["sources"].append(deepcopy(resource_v2["sources"][0]))
        source_v2 = resource_v2["sources"][i_source]
        source_v2.update(
            {
                "title": source.get("title"),
                "description": source.get("description"),
                "path": source.get("path"),
                "publicationYear": None,
                "authors": [],
            },
        )
        ___v2_populate_source_licenses(source_v2, source.get("licenses", []))


def ___v2_populate_source_licenses(source_v2: dict, licenses: list) -> None:
    """Populate licenses in source_v2 from licenses in v1.6."""
    for i_license, license_entry in enumerate(licenses):
        if i_license >= len(source_v2["licenses"]):
            source_v2["licenses"].append(deepcopy(source_v2["licenses"][0]))
        source_v2["licenses"][i_license].update(license_entry)
        source_v2["licenses"][i_license]["copyrightStatement"] = None


def ___v2_populate_contributors(resource_v2: dict, contributors: list) -> None:
    """Populate contributors in resource_v2 from contributors in v1.6."""
    for i_contribution, contributor in enumerate(contributors):
        if i_contribution >= len(resource_v2["contributors"]):
            resource_v2["contributors"].append(deepcopy(resource_v2["contributors"][0]))
        contributor_v2 = resource_v2["contributors"][i_contribution]
        contributor_v2.update(
            {
                "title": contributor.get("title"),
                "path": contributor.get("path"),
                "organization": contributor.get("organization"),
                "date": contributor.get("date"),
                "object": contributor.get("object"),
                "comment": contributor.get("comment"),
            },
        )


def ___v2_populate_licenses(resource_v2: dict, licenses: list) -> None:
    """Populate licenses in resource_v2 from licenses in v1.6."""
    for i_license, license_entry in enumerate(licenses):
        if i_license >= len(resource_v2["licenses"]):
            resource_v2["licenses"].append(deepcopy(resource_v2["licenses"][0]))
        resource_v2["licenses"][i_license].update(license_entry)
        resource_v2["licenses"][i_license]["copyrightStatement"] = None


def ___v2_populate_schema_fields(resource_v2: dict, resource: dict) -> None:
    """Populate schema fields in resource_v2 from resource in v1.6."""
    for i_field, field in enumerate(resource.get("schema", {}).get("fields", [])):
        if i_field >= len(resource_v2["schema"]["fields"]):
            resource_v2["schema"]["fields"].append(deepcopy(resource_v2["schema"]["fields"][0]))
        schema_field_v2 = resource_v2["schema"]["fields"][i_field]
        schema_field_v2.update(field)
        schema_field_v2["nullable"] = None




def __convert_oep_201_to_202(metadata: dict) -> dict:
    """
    Convert metadata with version "OEP-1.6.0" to "OEMetadata-2.0.1" using the v2.0 template.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary in v1.6 format

    Returns
    -------
    dict
        Updated metadata dictionary in v2.0 format
    """
    metadata_v2 = deepcopy(get_metadata_specification("OEMetadata-2.0.2").template)




def __convert_oep_202_to_203(metadata: dict) -> dict:
    """
    Convert metadata with version "OEP-1.6.0" to "OEMetadata-2.0.1" using the v2.0 template.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary in v1.6 format

    Returns
    -------
    dict
        Updated metadata dictionary in v2.0 format
    """
    metadata_v2 = deepcopy(get_metadata_specification("OEMetadata-2.0.3").template)    

METADATA_CONVERSIONS = {
    ("OEP-1.5.2", "OEP-1.6.0"): __convert_oep_152_to_160,
    ("OEP-1.6.0", "OEMetadata-2.0.1"): __convert_oep_160_to_201,
}
