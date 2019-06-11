from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from metadata_tool.structure import License
import os, glob
import json

def generate_license_structures():
    env = Environment(
        loader=FileSystemLoader(""),
        autoescape=select_autoescape(['python'])
    )
    working_directory = "license-list-data/json/details"
    template = env.get_template('templates/license.py')
    licenses = []
    for file_name in os.listdir(working_directory):
        if file_name.endswith(".json"):
            with open(os.path.join(working_directory,file_name), "r") as open_file:
                license_json = json.loads(open_file.read())
                comment = license_json.get("licenseComments")
                if comment is not None:
                    comment = _encode(comment)
                license=License(
                    path="http://spdx.org/licenses/%s"%license_json["licenseId"],
                    name=_encode(license_json["name"]),
                    identifier=_encode(license_json["licenseId"]),
                    other_references=[_encode(r) for r in license_json["seeAlso"]],
                    text=_encode(license_json["licenseText"]),
                    comment=comment)
                display_name=License.instance_name_from_id(license_json["licenseId"])
                licenses.append((license, display_name))

    with open("licenses.py","w") as outfile:
        outfile.write(template.render(licenses=licenses))

def _encode(s:str):
    return str(s.encode('unicode_escape').decode("utf-8")).replace('"', '\\"')

if __name__=="__main__":
    generate_license_structures()
