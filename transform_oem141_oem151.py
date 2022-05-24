import os
import json
import copy

## oem templates
oem141 = {'name': '', 'title': '', 'id': '', 'description': '', 'language': [''], 'keywords': [''], 'publicationDate': '', 'context': {'homepage': '', 'documentation': '', 'sourceCode': '', 'contact': '', 'grantNo': '', 'fundingAgency': '', 'fundingAgencyLogo': '', 'publisherLogo': ''}, 'spatial': {'location': '', 'extent': '', 'resolution': ''}, 'temporal': {'referenceDate': '', 'timeseries': {'start': '', 'end': '', 'resolution': '', 'alignment': '', 'aggregationType': ''}}, 'sources': [{'title': '', 'description': '', 'path': '', 'licenses': [{'name': '', 'title': '', 'path': '', 'instruction': '', 'attribution': ''}]}, {'title': '', 'description': '', 'path': '', 'licenses': [{'name': '', 'title': '', 'path': '', 'instruction': '', 'attribution': ''}]}], 'licenses': [{'name': '', 'title': '', 'path': '', 'instruction': '', 'attribution': ''}], 'contributors': [{'title': '', 'email': '', 'date': '', 'object': '', 'comment': ''}, {'title': '', 'email': '', 'date': '', 'object': '', 'comment': ''}], 'resources': [{'profile': '', 'name': '', 'path': '', 'format': '', 'encoding': '', 'schema': {'fields': [{'name': '', 'description': '', 'type': '', 'unit': ''}, {'name': '', 'description': '', 'type': '', 'unit': ''}], 'primaryKey': [''], 'foreignKeys': [{'fields': [''], 'reference': {'resource': '', 'fields': ['']}}]}, 'dialect': {'delimiter': '', 'decimalSeparator': '.'}}], 'review': {'path': '', 'badge': ''}, 'metaMetadata': {'metadataVersion': 'OEP-1.4.1', 'metadataLicense': {'name': 'CC0-1.0', 'title': 'Creative Commons Zero v1.0 Universal', 'path': 'https://creativecommons.org/publicdomain/zero/1.0/'}}, '_comment': {'metadata': 'Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/organisation/wiki/metadata)', 'dates': 'Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ssÂ±hh)', 'units': 'Use a space between numbers and units (100 m)', 'languages': 'Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)', 'licenses': 'License name must follow the SPDX License List (https://spdx.org/licenses/)', 'review': 'Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/wiki)', 'null': 'If not applicable use (null)'}}
oem151 = {'name': None, 'title': None, 'id': None, 'description': None, 'language': [None], 'subject': [{'name': None, 'path': None}], 'keywords': [None], 'publicationDate': None, 'context': {'homepage': None, 'documentation': None, 'sourceCode': None, 'contact': None, 'grantNo': None, 'fundingAgency': None, 'fundingAgencyLogo': None, 'publisherLogo': None}, 'spatial': {'location': None, 'extent': None, 'resolution': None}, 'temporal': {'referenceDate': None, 'timeseries': [{'start': None, 'end': None, 'resolution': None, 'alignment': None, 'aggregationType': None}, {'start': None, 'end': None, 'resolution': None, 'alignment': None, 'aggregationType': None}]}, 'sources': [{'title': None, 'description': None, 'path': None, 'licenses': [{'name': None, 'title': None, 'path': None, 'instruction': None, 'attribution': None}]}, {'title': None, 'description': None, 'path': None, 'licenses': [{'name': None, 'title': None, 'path': None, 'instruction': None, 'attribution': None}]}], 'licenses': [{'name': None, 'title': None, 'path': None, 'instruction': None, 'attribution': None}], 'contributors': [{'title': None, 'email': None, 'date': None, 'object': None, 'comment': None}], 'resources': [{'profile': None, 'name': None, 'path': None, 'format': None, 'encoding': None, 'schema': {'fields': [{'name': None, 'description': None, 'type': None, 'unit': None, 'isAbout': [{'name': None, 'path': None}], 'valueReference': [{'value': None, 'name': None, 'path': None}]}, {'name': None, 'description': None, 'type': None, 'unit': None, 'isAbout': [{'name': None, 'path': None}], 'valueReference': [{'value': None, 'name': None, 'path': None}]}], 'primaryKey': [None], 'foreignKeys': [{'fields': [None], 'reference': {'resource': None, 'fields': [None]}}]}, 'dialect': {'delimiter': None, 'decimalSeparator': '.'}}], '@id': None, '@context': None, 'review': {'path': None, 'badge': None}, 'metaMetadata': {'metadataVersion': 'OEP-1.5.0', 'metadataLicense': {'name': 'CC0-1.0', 'title': 'Creative Commons Zero v1.0 Universal', 'path': 'https://creativecommons.org/publicdomain/zero/1.0/'}}, '_comment': {'metadata': 'Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)', 'dates': 'Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ssÂ±hh)', 'units': 'Use a space between numbers and units (100 m)', 'languages': 'Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)', 'licenses': 'License name must follow the SPDX License List (https://spdx.org/licenses/)', 'review': 'Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)', 'null': 'If not applicable use: null', 'todo': 'If a value is not yet available, use: todo'}}

## make copy of empty oem151 template
v151_template = copy.deepcopy(oem151)

## select oem151 keys

context_keys = (list(oem151["context"].keys()))
spatial_keys = (list(oem151["spatial"].keys()))
review_keys = (list(oem151["review"].keys()))

## load oem141 for conversion to oem151
json_path = './JSON/v141'
json_files = os.listdir(json_path)
all_json_files_paths = [json_path + "/" + json_file for json_file in json_files]

## open all files to convert from oem141 to oem151
#for json_file in all_json_files_paths:

with open(all_json_files_paths[1]) as json_file:
    v141_file = json.load(json_file)

## update oem151 template with values from oem141

# Update key-values on 1st level, that contain information that need to be updated. Note: '_comment'-key and 'metaMetadata' is not copied from oeo141
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
    if key in v141_file:
        if v141_file[key] != "":
            v151_template[key] = v141_file[key]
    else:
        print(f'The key:[{key}] is not present in oemetadata v141, despite being declared in the OEM v141 template ')

# Update review keys
for key in review_keys:
    if key in v141_file["review"].keys():
        if v141_file["review"][key] != "":
            v151_template["review"][key] = v141_file["review"][key]

# Update context keys
for key in context_keys:
    if key in v141_file["context"].keys():
        if v141_file["context"][key] != "":
            v151_template["context"][key] = v141_file["context"][key]

# Update spatial keys
for key in spatial_keys:
    if key in v141_file["spatial"].keys():
        if v141_file["spatial"][key] != "":
            v151_template["spatial"][key] = v141_file["spatial"][key]
