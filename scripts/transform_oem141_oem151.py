import os
import json
from copy import deepcopy


"""
This script transforms OEMetadata v1.4.1 (oem141) into OEMetadata v.1.5.1 (oem151).
It does so by backfilling the key-values from oem141 files into an empty oem151 template.json.
Default keys and values from oem151 are provided, if keys are not used or values are not filled in oem141.
The method applies for all key-values, except for the ‘foreignKeys‘ key, which is a direct copy of the list in oem141
and the '_comment' and 'metaMetadata' key, which are not processed, as new oem151 information is provided

Files are read from ./JSON/v141
Files are saved to ./JSON/v151

"""

# create directories or pass if exist
oem_versions = ["v141", "v151"]
for oem in oem_versions:
    try:
        os.makedirs(f"./JSON/{oem}")
    except FileExistsError:
        print(f"The directory: ./JSON/{oem} exists already")
        pass

# load oem141 file paths
json_path = "./JSON/v141"
json_files = os.listdir(json_path)
all_json_files_paths = [json_path + "/" + json_file for json_file in json_files]

# oem151 template
oem151 = {
    "name": None,
    "title": None,
    "id": None,
    "description": None,
    "language": [None],
    "subject": [{"name": None, "path": None}],
    "keywords": [None],
    "publicationDate": None,
    "context": {
        "homepage": None,
        "documentation": None,
        "sourceCode": None,
        "contact": None,
        "grantNo": None,
        "fundingAgency": None,
        "fundingAgencyLogo": None,
        "publisherLogo": None,
    },
    "spatial": {"location": None, "extent": None, "resolution": None},
    "temporal": {
        "referenceDate": None,
        "timeseries": [
            {
                "start": None,
                "end": None,
                "resolution": None,
                "alignment": None,
                "aggregationType": None,
            },
            {
                "start": None,
                "end": None,
                "resolution": None,
                "alignment": None,
                "aggregationType": None,
            },
        ],
    },
    "sources": [
        {
            "title": None,
            "description": None,
            "path": None,
            "licenses": [
                {
                    "name": None,
                    "title": None,
                    "path": None,
                    "instruction": None,
                    "attribution": None,
                }
            ],
        },
        {
            "title": None,
            "description": None,
            "path": None,
            "licenses": [
                {
                    "name": None,
                    "title": None,
                    "path": None,
                    "instruction": None,
                    "attribution": None,
                }
            ],
        },
    ],
    "licenses": [
        {
            "name": None,
            "title": None,
            "path": None,
            "instruction": None,
            "attribution": None,
        }
    ],
    "contributors": [
        {"title": None, "email": None, "date": None, "object": None, "comment": None}
    ],
    "resources": [
        {
            "profile": None,
            "name": None,
            "path": None,
            "format": None,
            "encoding": None,
            "schema": {
                "fields": [
                    {
                        "name": None,
                        "description": None,
                        "type": None,
                        "unit": None,
                        "isAbout": [{"name": None, "path": None}],
                        "valueReference": [{"value": None, "name": None, "path": None}],
                    },
                    {
                        "name": None,
                        "description": None,
                        "type": None,
                        "unit": None,
                        "isAbout": [{"name": None, "path": None}],
                        "valueReference": [{"value": None, "name": None, "path": None}],
                    },
                ],
                "primaryKey": [None],
                "foreignKeys": [
                    {
                        "fields": [None],
                        "reference": {"resource": None, "fields": [None]},
                    }
                ],
            },
            "dialect": {"delimiter": None, "decimalSeparator": "."},
        }
    ],
    "@id": None,
    "@context": None,
    "review": {"path": None, "badge": None},
    "metaMetadata": {
        "metadataVersion": "OEP-1.5.0",
        "metadataLicense": {
            "name": "CC0-1.0",
            "title": "Creative Commons Zero v1.0 Universal",
            "path": "https://creativecommons.org/publicdomain/zero/1.0/",
        },
    },
    "_comment": {
        "metadata": "Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)",
        "dates": "Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ssÂ±hh)",
        "units": "Use a space between numbers and units (100 m)",
        "languages": "Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
        "licenses": "License name must follow the SPDX License List (https://spdx.org/licenses/)",
        "review": "Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)",
        "null": "If not applicable use: null",
        "todo": "If a value is not yet available, use: todo",
    },
}

# create oem template with empty lists in keys: sources, temporal, licenses, contributers, resources
oem151_empty_lists = deepcopy(oem151)
keys_to_empty = ["sources", "temporal", "licenses", "contributors", "resources"]
for keys in keys_to_empty:
    oem151_empty_lists[keys] = []

# make copy of empty oem151 template
v151_temp_backfill_clean = deepcopy(oem151_empty_lists)

# prepare oem151 keys and dicts for later reference during backfill

context_keys = list(oem151["context"].keys())
spatial_keys = list(oem151["spatial"].keys())
review_keys = list(oem151["review"].keys())

contributer_dict = deepcopy(oem151["contributors"][0])

licenses_keys = list(oem151["licenses"][0].keys())
licenses_dict = deepcopy(oem151["licenses"][0])

temporal_dict = deepcopy(oem151["temporal"])
temporal_dict["timeseries"] = [temporal_dict["timeseries"][0]]
temporal_keys = list(oem151["temporal"].keys())
ts_keys = list(oem151["temporal"]["timeseries"][0].keys())

sources_dict = deepcopy(oem151["sources"][0])
sources_licenses_keys = list(oem151["sources"][0]["licenses"][0])
sources_licenses_dict = deepcopy(oem151["sources"][0]["licenses"][0])

resources_dict = deepcopy(oem151["resources"][0])
resources_dict["schema"]["fields"] = []
resources_schema_keys = list(oem151["resources"][0]["schema"])
resources_dialect_dict = deepcopy(oem151["resources"][0]["dialect"])
resources_schema_fields = deepcopy(oem151["resources"][0]["schema"]["fields"][0])

# backfill oem141 to oem151 for all json_files in ./JSON/v141
for json_file in all_json_files_paths:

    # save filename for output
    filename = json_file.split("/")[-1].split(".")[0]

    # open oem141 files
    with open(json_file, encoding="utf-8") as json_file:
        v141_file = json.load(json_file)

    # create a clean and empty 'v151_temp_backfill' for each processed oem141 JSON
    v151_temp_backfill = deepcopy(v151_temp_backfill_clean)

    # start backfill
    # Note: '_comment' and 'metaMetadata' are not processed, as new oem151 information is provided.
    # backfill key-values on 1st level.
    first_level_keys = [
        "name",
        "title",
        "id",
        "description",
        "language",
        "keywords",
        "publicationDate",
    ]

    for key in first_level_keys:
        if key in v141_file and v141_file[key] != "":
            v151_temp_backfill[key] = v141_file[key]
        else:
            print(
                f"The key:[{key}] is not present in oemetadata v141, despite being declared in the OEM v141 template "
            )

    # backfill review keys
    for key in review_keys:
        if key in v141_file["review"].keys() and v141_file["review"][key] != "":
            v151_temp_backfill["review"][key] = v141_file["review"][key]

    # backfill context keys
    for key in context_keys:
        if key in v141_file["context"].keys() and v141_file["context"][key] != "":
            v151_temp_backfill["context"][key] = v141_file["context"][key]

    # backfill spatial keys
    for key in spatial_keys:
        if key in v141_file["spatial"].keys() and v141_file["spatial"][key] != "":
            v151_temp_backfill["spatial"][key] = v141_file["spatial"][key]

    # backfill contributors
    for index, dict in enumerate(v141_file["contributors"]):
        # add own contributer_dict for each contributer
        v151_temp_backfill["contributors"].append(deepcopy(contributer_dict))
        for key, value in dict.items():
            if v141_file["contributors"][index][key] != "":
                v151_temp_backfill["contributors"][index][key] = value

    # backfill licenses
    for index, dict in enumerate(v141_file["licenses"]):
        # add own licenses_dict for each licenses
        v151_temp_backfill["licenses"].append(deepcopy(licenses_dict))
        for key, value in dict.items():
            if v141_file["licenses"][index][key] != "":
                v151_temp_backfill["licenses"][index][key] = value

    # backfill temporal
    # Note: in oem141 only 1 temporal_dict should exist, as the key 'temporal' is just dict and not list, as in oem151.
    # add own temporal_dict for each temporal.
    v151_temp_backfill["temporal"] = temporal_dict

    for key in temporal_keys:
        if key == "timeseries":
            for timeseries_key in ts_keys:
                if v141_file["temporal"][key] is not None and timeseries_key in list(
                    v141_file["temporal"]["timeseries"].keys()
                ):
                    v151_temp_backfill["temporal"][key][0][timeseries_key] = v141_file[
                        "temporal"
                    ][key][timeseries_key]
                else:
                    print(f"{timeseries_key} is not used and filled in oem141")

        elif key in v141_file["temporal"].keys():
            if v141_file["temporal"][key] != "":
                v151_temp_backfill["temporal"][key] = v141_file["temporal"][key]

    # backfill sources
    for index, dict in enumerate(v141_file["sources"]):
        # add own sources_dict for each source
        v151_temp_backfill["sources"].append(deepcopy(sources_dict))
        for key, value in dict.items():
            if key == "licenses" and v141_file["sources"][index]["licenses"]:
                for src_lc_key in sources_licenses_keys:
                    if (
                        src_lc_key in list(v141_file["sources"][index]["licenses"][0])
                        and v141_file["sources"][index]["licenses"][0][src_lc_key] != ""
                    ):
                        v151_temp_backfill["sources"][index][key][0][
                            src_lc_key
                        ] = value[0][src_lc_key]

            elif key == "licenses" and not v141_file["sources"][index]["licenses"]:
                v151_temp_backfill["sources"][index][key][0] = sources_licenses_dict

            elif v141_file["sources"][index][key] != "":
                v151_temp_backfill["sources"][index][key] = value

    # backfill resources
    for index, dict in enumerate(v141_file["resources"]):
        # add own resources_dict for each resource
        v151_temp_backfill["resources"].append(deepcopy(resources_dict))
        for key, value in dict.items():
            if key == "schema":
                if "primaryKey" in value:
                    v151_temp_backfill["resources"][index][key][
                        "primaryKey"
                    ] = v141_file["resources"][index][key]["primaryKey"]
                if "foreignKeys" in value:
                    v151_temp_backfill["resources"][index][key][
                        "foreignKeys"
                    ] = v141_file["resources"][index][key]["foreignKeys"]

                if "fields" in value:
                    for index_fields, dict_fields in enumerate(
                        v141_file["resources"][index]["schema"]["fields"]
                    ):
                        v151_temp_backfill["resources"][index]["schema"][
                            "fields"
                        ].append(deepcopy(resources_schema_fields))
                        for key_fields, value_fields in dict_fields.items():
                            v151_temp_backfill["resources"][index]["schema"]["fields"][
                                index_fields
                            ][key_fields] = value_fields

            elif key == "dialect":
                if "delimiter" in value:
                    v151_temp_backfill["resources"][index][key]["delimiter"] = value[
                        "delimiter"
                    ]
                elif "decimalSeparator" in value:
                    v151_temp_backfill["resources"][index][key][
                        "decimalSeparator"
                    ] = value["decimalSeparator"]

            elif v141_file["resources"][index][key] != "":
                v151_temp_backfill["resources"][index][key] = value

    # save backfilled oem151 template to json in ./JSON/v151
    with open(
        f"./JSON/v151/{filename}.metadata_oem151.json", "w", encoding="utf-8"
    ) as outfile:
        json.dump(v151_temp_backfill, outfile, indent=4, ensure_ascii=False)
