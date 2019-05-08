#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json

from metadata_tool import structure
from metadata_tool.dialects.base.parser import Parser


class JSONParser(Parser):
    def is_valid(self, inp: str):
        """Checks the validity of a JSON string

        Parameters
        ----------
        inp: str
            The JSON string to be checked.

        Returns
        -------
        bool
            True if valid JSON, False otherwise.
        """

        try:
            json.loads(inp)
        except ValueError:
            return False
        return True


class JSONParser_1_3(JSONParser):
    def is_valid(self, inp: str):
        if not super(self, JSONParser_1_3).is_valid(inp):
            return False
        try:
            self.assert_1_3_metastring(inp)
        except:
            return False
        else:
            return True

    def parse(self, inp: str):
        json_old = json.loads(inp)

        # In the following a new structure is set. The yet implemented version is for metadata v1.2 to v1.3.

        # context section
        context = structure.Context(
            homepage=None,
            documentation=None,
            source_code=None,
            contact=None,
            grant_number=None,
        )

        # filling the spatial section
        old_spatial = json_old["spatial"]
        spatial = structure.Spatial(
            location="",
            extend=old_spatial["extent"],
            resolution=old_spatial["resolution"],
        )

        # filling the temporal section
        temporal = structure.Temporal(
            reference_date=json_old["temporal"]["reference_date"],
            start=None,
            end=None,
            resolution=None,
        )

        # filling the source section
        sources = [
            structure.Source(
                title=old_source["name"],
                description=old_source["description"],
                path=old_source["url"],
                source_license=None,
                source_copyright=old_source["copyright"],
            )
            for old_source in json_old["sources"]
        ]

        # filling the license section
        old_license = json_old["license"]
        licenses = [
            structure.License(
                name=old_license["id"],
                title=old_license["name"],
                path=old_license["url"],
                instruction=old_license["instruction"],
                attribution=old_license["copyright"],
            )
        ]

        # filling the contributers section
        contributors = [
            structure.Contributor(
                title=old_contributor["name"],
                email=old_contributor["email"],
                date=old_contributor["date"],
                obj="",
                comment=old_contributor["comment"],
            )
            for old_contributor in json_old["contributors"]
        ]

        # extending with script-user information

        resources = []
        for resource in json_old["resources"]:
            fields = [
                structure.Field(
                    name=field["name"],
                    description=field["description"],
                    field_type=None,
                    unit=field["unit"],
                )
                for field in resource["fields"]
            ]
            schema = structure.Schema(fields=fields, primary_key=[], foreign_keys=[])
            resources.append(
                structure.Resource(
                    profile=None,
                    name=None,
                    path=None,
                    resource_format="PostgreSQL",
                    encoding=None,
                    schema=schema,
                )
            )

        review = structure.Review(path=None, badge=None)

        comment = structure.MetaComment(
            metadata_info="Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/organisation/wiki/metadata)",
            dates="Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
            units="Use a space between numbers and units (100 m)",
            languages="Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
            licenses="License name must follow the SPDX License List (https://spdx.org/licenses/",
            review="Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/wiki)",
            none="If not applicable use (none)",
        )

        metadata = structure.OEPMetadata(
            name=None,
            title=json_old["title"],
            identifier=None,
            description=json_old["description"],
            languages=json_old["language"],
            keywords=[],
            publication_date=None,
            context=context,
            spatial=spatial,
            temporal=temporal,
            sources=sources,
            object_licenses=licenses,
            contributors=contributors,
            resources=resources,
            review=review,
            comment=comment,
        )
        return metadata


class JSONParser_1_4(JSONParser):
    def is_valid(self, inp: str):
        if not super(self, JSONParser_1_4).is_valid(inp):
            return False
        try:
            self.assert_1_3_metastring(inp)
        except:
            return False
        else:
            return True

    def parse(self, inp: str):
        json_old = json.loads(inp)

        # In the following a new structure is set. The yet implemented version is for metadata v1.2 to v1.3.

        # context section
        inp_context = json_old["context"]
        context = structure.Context(
            homepage=inp_context["homepage"],
            documentation=inp_context["documentation"],
            source_code=inp_context["sourceCode"],
            contact=inp_context["contact"],
            grant_number=inp_context["grantNo"],
        )

        # filling the spatial section
        old_spatial = json_old["spatial"]
        spatial = structure.Spatial(
            location=old_spatial["location"],
            extend=old_spatial["extent"],
            resolution=old_spatial["resolution"],
        )

        # filling the temporal section
        inp_temporal = json_old["temporal"]
        temporal = structure.Temporal(
            reference_date=datetime.datetime.strptime(
                inp_temporal["referenceDate"], "%Y-%m-%d"
            ),
            start=datetime.datetime.strptime(
                inp_temporal["start"] + "00", "%Y-%m-%dT%H:%M%z"
            ),
            end=datetime.datetime.strptime(
                inp_temporal["end"] + "00", "%Y-%m-%dT%H:%M%z"
            ),
            resolution=inp_temporal["resolution"],
        )

        # filling the source section
        sources = [
            structure.Source(
                title=old_source["title"],
                description=old_source["description"],
                path=old_source["path"],
                source_license=structure.License(
                    None, old_source["license"], None, None, None
                ),
                source_copyright=old_source["copyright"],
            )
            for old_source in json_old["sources"]
        ]

        # filling the license section
        licenses = [
            structure.License(
                name=old_license["name"],
                title=old_license["title"],
                path=old_license["path"],
                instruction=old_license["instruction"],
                attribution=old_license["attribution"],
            )
            for old_license in json_old["licenses"]
        ]

        # filling the contributers section
        contributors = [
            structure.Contributor(
                title=old_contributor["title"],
                email=old_contributor["email"],
                date=old_contributor["date"],
                obj=old_contributor["object"],
                comment=old_contributor["comment"],
            )
            for old_contributor in json_old["contributors"]
        ]

        # extending with script-user information

        resources = []
        for resource in json_old["resources"]:
            fields = [
                structure.Field(
                    name=field["name"],
                    description=field["description"],
                    field_type=field["type"],
                    unit=field["unit"],
                )
                for field in resource["schema"]["fields"]
            ]
            schema = structure.Schema(
                fields=fields,
                primary_key=resource["schema"]["primaryKey"],
                foreign_keys=[
                    structure.ForeignKey(
                        fields=fk["fields"],
                        reference=structure.Reference(
                            resource=fk["reference"]["resource"],
                            fields=fk["reference"]["fields"],
                        ),
                    )
                    for fk in resource["schema"]["foreignKeys"]
                ],
            )
            resources.append(
                structure.Resource(
                    profile=resource["profile"],
                    name=resource["name"],
                    path=resource["path"],
                    resource_format=resource["format"],
                    encoding=resource["encoding"],
                    schema=schema,
                )
            )

        inp_review = json_old["review"]
        review = structure.Review(path=inp_review["path"], badge=inp_review["badge"])

        inp_comment = json_old["_comment"]
        comment = structure.MetaComment(
            metadata_info=inp_comment["metadata"],
            dates=inp_comment["dates"],
            units=inp_comment["units"],
            languages=inp_comment["languages"],
            licenses=inp_comment["licenses"],
            review=inp_comment["review"],
            none=inp_comment["none"],
        )

        metadata = structure.OEPMetadata(
            name=json_old["name"],
            title=json_old["title"],
            identifier=json_old["id"],
            description=json_old["description"],
            languages=json_old["language"],
            keywords=json_old["keywords"],
            publication_date=datetime.datetime.strptime(
                json_old["publicationDate"], "%Y-%m-%d"
            ),
            context=context,
            spatial=spatial,
            temporal=temporal,
            sources=sources,
            object_licenses=licenses,
            contributors=contributors,
            resources=resources,
            review=review,
            comment=comment,
        )
        return metadata

    def assert_1_3_metastring(self, json_string: str):
        """Checks string conformity to OEP Metadata Standard Version 1.3

        Parameters
        ----------
        json_string: str
            The JSON string to be checked.

        Returns
        -------
        bool
            True if valid, Raises Exception otherwise.
        """

        keys = [
            "title",
            "description",
            "language",
            "spatial",
            "temporal",
            "sources",
            "license",
            "contributors",
            "resources",
            "metadata_version",
        ]
        subkeys_spatial = ["location", "extent", "resolution"]
        subkeys_temporal = ["reference_date", "start", "end", "resolution"]
        subkeys_license = ["id", "name", "version", "url", "instruction", "copyright"]
        object_subkeys = {
            "spatial": subkeys_spatial,
            "temporal": subkeys_temporal,
            "license": subkeys_license,
        }
        subkeys_sources = [
            "name",
            "description",
            "url",
            "license",
            "copyright",
        ]  # in list of objects
        subkeys_contributors = [
            "name",
            "email",
            "date",
            "comment",
        ]  # in list of objects
        subkeys_resources = ["name", "format", "fields"]  # in list of objects
        list_subkeys = {
            "sources": subkeys_sources,
            "contributors": subkeys_contributors,
            "resources": subkeys_resources,
        }
        subkeys_resources_fields = ["name", "description", "unit"]  # in list of objects

        json_dict = json.loads(json_string)
        try:
            # check if all top level keys are present
            for i in keys:
                if not i in json_dict.keys():
                    raise Exception(
                        'The String did not contain the key "{0}"'.format(i)
                    )
            # check for all keys in second level objects
            for key in object_subkeys:
                for subkey in object_subkeys[key]:
                    if not subkey in json_dict[key]:
                        raise Exception(
                            'The "{0}" object did not contain a "{1}" key'.format(
                                key, subkey
                            )
                        )
            # check for all objects in lists if they contain all required keys
            for key in list_subkeys:
                for list_element in json_dict[key]:
                    for subkey in list_subkeys[key]:
                        if not subkey in list_element:
                            raise Exception(
                                'An object in "{0}" is missing a "{1}" key'.format(
                                    key, subkey
                                )
                            )
        except Exception as error:
            print(
                "The input String does not conform to metadatastring version 1.3 standard"
            )
            print(error)

    # TODO make function check all subkeys as well
    def has_rogue_keys(self, json_string):
        """Checks all keys if they are part of the metadata specification. Gives warnings if not.

        Parameters
        ----------
        json_string: str
            The JSON string to be checked.

        Returns
        -------
        """

        json_dict = json.loads(json_string)
        allowed_keys = [
            "title",
            "description",
            "language",
            "spatial",
            "temporal",
            "sources",
            "license",
            "contributors",
            "resources",
            "metadata_version",
        ]
        for j in json_dict.keys():
            if not j in allowed_keys:
                print('Warning: "{0}" is not among the allowed keys'.format(j))

    def get_table_name(self, metadata_file):
        """Provides the tablename information from the metadata_file

        Parameters
        ----------
        metadata_file: str
            The metadata script from where the tablename is extracted from.

        Returns
        -------
        tablename: str
            returns the tablename.
        """

        raise NotImplementedError
