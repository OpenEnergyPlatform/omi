"""Conversion functions for metadata version "OEP-1.6.0" to "OEMetadata-2.0"."""

from copy import deepcopy

from omi.base import get_metadata_specification

# use utils.find_spatial_resolution_value_and_unit
from omi.conversions.utils import find_temporal_resolution_value_and_unit


def convert_oep_160_to_20(metadata: dict) -> dict:
    """
    Convert metadata with version "OEP-1.6.0" to "OEMetadata-2.0" using the v2.0 template.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary in v1.6 format

    Returns
    -------
    dict
        Updated metadata dictionary in v2.0 format
    """
    metadata_v2 = deepcopy(get_metadata_specification("OEMetadata-2.0").template)

    # Update to v2 context URL
    metadata_v2[
        "@context"
    ] = "https://raw.githubusercontent.com/OpenEnergyPlatform/oemetadata/production/oemetadata/v2/v20/context.json"
    metadata_v2["name"] = metadata_v2["title"] = metadata_v2["description"] = ""

    metadata_v2["@id"] = None

    # Populate metadata v2 resources
    for i, resource in enumerate(metadata.get("resources", [])):
        resource_v2 = ___v2_ensure_resource_entry(metadata_v2, i)
        ___v2_populate_resource_v2(resource_v2, metadata, resource)

    # Update metaMetadata section
    metadata_v2["metaMetadata"]["metadataVersion"] = "OEMetadata-2.0.4"
    metadata_v2["metaMetadata"]["metadataLicense"] = metadata.get("metaMetadata", {}).get("metadataLicense")

    return metadata_v2


def ___v2_ensure_resource_entry(metadata_v2: dict, index: int) -> dict:
    """Ensure a resource entry exists in metadata_v2 resources for the given index."""
    if index >= len(metadata_v2["resources"]):
        metadata_v2["resources"].append(deepcopy(metadata_v2["resources"][0]))
    return metadata_v2["resources"][index]


def ___v2_populate_resource_v2(resource_v2: dict, metadata: dict, resource: dict) -> None:  # noqa: C901
    """Populate resource_v2 fields based on metadata and resource from v1.6."""
    # Bulk update keys without
    resource_v2.update(
        {
            "@id": metadata.get("@id"),
            "name": metadata.get("name", "") or "",
            "title": metadata.get("title"),
            "path": metadata.get("id"),
            "description": metadata.get("description"),
            "publicationDate": metadata.get("publicationDate"),
            "type": "Table",
            "format": resource.get("format"),
            "encoding": resource.get("encoding"),
        },
    )

    if metadata.get("language"):
        if isinstance(metadata.get("language"), str):
            resource_v2["languages"].pop()
            resource_v2["languages"].append(metadata.get("language", [""]) or [])
        if isinstance(metadata.get("language"), list):
            resource_v2["languages"].pop()
            resource_v2["languages"].extend(metadata.get("language", [""]) or [])

    if metadata.get("keywords"):
        resource_v2["keywords"] = metadata.get("keywords", [""]) or []

    # Update metadata v2 subject key -> path to @id
    ___v2_populate_subjects(resource_v2, metadata.get("subject", []) or [])

    if metadata.get("context"):
        resource_v2["context"].update(metadata.get("context"))

    # Set to null to avoid validation errors: URI
    resource_v2["spatial"]["location"]["@id"] = None
    resource_v2["spatial"]["location"]["address"] = (metadata.get("spatial", {}) or {}).get("location")

    unpack = resource_v2["spatial"]["location"]["address"]
    resource_v2["spatial"]["location"]["address"] = ", ".join(unpack) if isinstance(unpack, list) else unpack

    # Set to null to avoid validation errors: URI
    resource_v2["spatial"]["extent"]["name"] = (metadata.get("spatial", {}) or {}).get("extent")
    resource_v2["spatial"]["extent"]["@id"] = None

    unpack = resource_v2["spatial"]["extent"]["name"]
    resource_v2["spatial"]["extent"]["name"] = ", ".join(unpack) if isinstance(unpack, list) else unpack

    resolution = (metadata.get("spatial", {}) or {}).get("resolution", "")
    if resolution:
        parts = resolution.split(" ", 1)

        if len(parts) == 2:  # noqa: PLR2004
            resource_v2["spatial"]["extent"]["resolutionValue"] = parts[0]
            resource_v2["spatial"]["extent"]["resolutionUnit"] = parts[1]
        elif len(parts) == 1 and parts[0]:
            # If there's a value but no unit, assign the value and use a default for the unit
            resource_v2["spatial"]["extent"]["resolutionValue"] = parts[0]
            resource_v2["spatial"]["extent"]["resolutionUnit"] = ""

    ___v2_populate_temporal(resource_v2, metadata.get("temporal", {}) or {})

    ___v2_populate_sources(resource_v2, metadata.get("sources", []) or [])
    ___v2_populate_contributors(resource_v2, metadata.get("contributors", []) or [])
    ___v2_populate_licenses(resource_v2, metadata.get("licenses", []) or [])
    ___v2_populate_schema_fields(resource_v2, resource)
    ___v2_populate_schema_primary_keys(resource_v2, resource)
    ___v2_populate_schema_foreign_keys(resource_v2, resource)

    if resource.get("dialect"):
        resource_v2["dialect"].update(resource.get("dialect", {}))

    if metadata.get("review"):
        resource_v2["review"].update(metadata.get("review", {}))


def ___v2_populate_subjects(resource_v2: list, subjects: list) -> None:
    """Populate licenses in source_v2 from licenses in v1.6."""
    if not subjects:
        resource_v2["subject"][0]["@id"] = None

    for i_subject, subject_entry in enumerate(subjects):
        if i_subject >= len(resource_v2["subject"]):
            resource_v2["subject"].append(deepcopy(resource_v2["subject"][0]))

        resource_v2["subject"][i_subject].update(rename_path_to_id(subject_entry))

        if resource_v2["subject"][i_subject]["@id"] == "":
            resource_v2["subject"][i_subject]["@id"] = None


def ___v2_populate_temporal(resource_v2: list, temporal: dict) -> None:
    """Populate temporal in resource_v2 from temporal in v1.6."""
    if isinstance(temporal.get("referenceDate"), str):
        resource_v2["temporal"]["referenceDate"] = temporal["referenceDate"]

    if "timeseries" not in temporal.keys():
        temporal["timeseries"] = []

    if not isinstance(temporal["timeseries"], list):
        temporal["timeseries"] = [temporal["timeseries"]]

    for i_timeseries, timeseries in enumerate(temporal.get("timeseries", []) or []):
        if i_timeseries >= len(resource_v2["temporal"]["timeseries"]):
            resource_v2["temporal"]["timeseries"].append(deepcopy(resource_v2["temporal"]["timeseries"][0]))

        if isinstance(timeseries, dict):
            resource_v2["temporal"]["timeseries"][i_timeseries].update(
                (k, timeseries[k])
                for k in resource_v2["temporal"]["timeseries"][i_timeseries].keys() & timeseries.keys()
            )

        if isinstance(timeseries.get("resolution"), str):
            value, unit = find_temporal_resolution_value_and_unit(timeseries["resolution"])
            resource_v2["temporal"]["timeseries"][i_timeseries].update(
                {
                    "resolutionValue": value,
                    "resolutionUnit": unit,
                },
            )


# sort out the code related to spatial information from above

# to add it to a new function, see below:
# def ___v2_populate_spatial(resource_v2: list, subjects: list) -> None:
#     """Populate licenses in source_v2 from licenses in v1.6."""
#     if not subjects:

#     for i_subject, subject_entry in enumerate(subjects):
#         if i_subject >= len(resource_v2["subject"]):


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
        ___v2_populate_source_licenses(source_v2, source.get("licenses", []) or [])


def ___v2_populate_source_licenses(source_v2: dict, licenses: list) -> None:
    """Populate licenses in source_v2 from licenses in v1.6."""
    for i_license, license_entry in enumerate(licenses):
        if i_license >= len(source_v2["sourceLicenses"]):
            source_v2["sourceLicenses"].append(deepcopy(source_v2["sourceLicenses"][0]))
        source_v2["sourceLicenses"][i_license].update(license_entry)
        source_v2["sourceLicenses"][i_license]["copyrightStatement"] = None


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

    # Due to some issue with the for loop nesting in some cases the conversion contribution node is
    # added twice. This is a workaround to avoid this issue.
    last_contributor = resource_v2["contributors"][len(resource_v2["contributors"]) - 1]
    if (
        isinstance(last_contributor.get("title"), str)
        and last_contributor.get("title", "") not in "Open Energy Platform oemetadata conversion to v2"
    ):
        resource_v2["contributors"].append(
            {
                "title": "Open Energy Platform oemetadata conversion to v2",
                "path": "https://github.com/OpenEnergyPlatform",
                "role": ["platform-maintainer"],
                "organization": "OpenEnergyFamily",
                "date": "2021-09-01",
                "object": "conversion of all metadata to oemetadata  version 2.0.4",
                "comment": "The conversion was done by the OpenEnergyFamily team using the OMI software."
                "We did our best to mitigate data loss. Most unexpected or incorrect metadata property"
                "entries will be lost.",
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
        if "id" in (schema_field_v2.get("name") or ""):
            schema_field_v2["nullable"] = False
        else:
            schema_field_v2["nullable"] = True

        # Here we handle special cases from input metadata as it will not always
        # follow the expected structure.
        # I decided to have certain fields empty meaning there fields will not hold
        # the information available by default (coming form the template.json):
        # - First handle isAbout to match the expected structure OR
        # make sure there is an empty array / list [] at the is about key
        # - Secondly handle valueReferences the same way
        for i in schema_field_v2.get("isAbout", []) or []:
            i.update(rename_path_to_id(i))

        if not schema_field_v2.get("isAbout"):  # noqa: SIM114
            schema_field_v2["isAbout"] = []
        elif "isAbout" not in field.keys():
            schema_field_v2["isAbout"] = []

        for i in schema_field_v2.get("valueReference", []) or []:
            i.update(rename_path_to_id(i))

        if not schema_field_v2.get("valueReference"):  # noqa: SIM114
            schema_field_v2["valueReference"] = []
        elif "valueReference" not in field.keys():
            schema_field_v2["valueReference"] = []


def rename_path_to_id(annotation_object: dict) -> dict:
    """Rename 'path' to '@id' in obj."""
    if "path" in annotation_object:
        annotation_object["@id"] = annotation_object.pop("path")
    return annotation_object


def ___v2_populate_schema_primary_keys(resource_v2: dict, resource: dict) -> None:
    """Populate schema fields in resource_v2 from resource in v1.6."""
    for i_pk, pk in enumerate(resource.get("schema", {}).get("primaryKey", []) or []):
        if i_pk >= len(resource_v2["schema"]["primaryKey"]):
            resource_v2["schema"]["primaryKey"].append(deepcopy(resource_v2["schema"]["primaryKey"][0]))

        if isinstance(pk, str):
            resource_v2["schema"]["primaryKey"].pop()
            resource_v2["schema"]["primaryKey"].append(pk)


def ___v2_populate_schema_foreign_keys(resource_v2: dict, resource: dict) -> None:
    """Populate schema fields in resource_v2 from resource in v1.6."""
    for i_fk, fk in enumerate(resource.get("schema", {}).get("foreignKeys", [])):
        if i_fk >= len(resource_v2["schema"]["foreignKeys"]):
            resource_v2["schema"]["foreignKeys"].append(deepcopy(resource_v2["schema"]["foreignKeys"][0]))

        if isinstance(fk, object):
            resource_v2["schema"]["foreignKeys"][i_fk].update(
                (k, resource["schema"]["foreignKeys"][i_fk][k])
                for k in resource_v2["schema"]["foreignKeys"][i_fk].keys()
                & resource["schema"]["foreignKeys"][i_fk].keys()
            )

        if (
            resource_v2["schema"]["foreignKeys"][i_fk]["reference"] is None
            and resource_v2["schema"]["foreignKeys"][i_fk]["fields"] is None
        ):
            resource_v2["schema"]["foreignKeys"].pop()
