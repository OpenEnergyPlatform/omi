#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from dateutil.parser import parse as parse_date

from omi import structure
from omi.dialects.base.parser import Parser


class JSONParser(Parser):
    def load_string(self, string: str, *args, **kwargs):
        return json.loads(string)

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

    def parse(self, json_old, *args, **kwargs):
        # context section
        context = structure.Context(
            homepage=None,
            documentation=None,
            source_code=None,
            contact=None,
            grant_number=None,
        )

        # filling the spatial section
        old_spatial = json_old.get("spatial")
        spatial = structure.Spatial(
            location=None,
            extent=old_spatial.get("extent"),
            resolution=old_spatial.get("resolution"),
        )

        # filling the temporal section
        temporal = structure.Temporal(
            reference_date=parse_date(json_old["temporal"].get("reference_date")),
            start=None,
            end=None,
            resolution=None,
            ts_orientation=None,
        )

        # filling the source section
        sources = [
            structure.Source(
                title=old_source.get("name"),
                description=old_source.get("description"),
                path=old_source.get("url"),
                source_license=None,
                source_copyright=old_source.get("copyright"),
            )
            for old_source in json_old.get("sources")
        ]

        # filling the license section
        old_license = json_old.get("license")
        licenses = [
            structure.TermsOfUse(
                lic=structure.License(
                    identifier=old_license.get("id"),
                    name=old_license.get("name"),
                    path=old_license.get("url"),
                    other_references=[],
                    text=None,
                ),
                instruction=old_license.get("instruction"),
                attribution=old_license.get("copyright"),
            )
        ]

        # filling the contributers section
        contributions = [
            structure.Contribution(
                contributor=structure.Person(
                    name=old_contributor.get("name"), email=old_contributor.get("email")
                ),
                date=parse_date(old_contributor.get("date")),
                obj=None,
                comment=old_contributor.get("comment"),
            )
            for old_contributor in json_old.get("contributors")
        ]

        # extending with script-user information

        resources = []
        for resource in json_old.get("resources"):
            fields = [
                structure.Field(
                    name=field.get("name"),
                    description=field.get("description"),
                    field_type=None,
                    unit=field.get("unit"),
                )
                for field in resource.get("fields", [])
            ]
            schema = structure.Schema(fields=fields, primary_key=None, foreign_keys=[])
            resources.append(
                structure.Resource(
                    profile=None,
                    name=resource.get("name"),
                    path=None,
                    resource_format="PostgreSQL",
                    encoding=None,
                    dialect=None,
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
            title=json_old.get("title"),
            identifier=None,
            description=json_old.get("description"),
            languages=json_old.get("language"),
            keywords=[],
            publication_date=None,
            context=context,
            spatial=spatial,
            temporal=temporal,
            sources=sources,
            terms_of_use=licenses,
            contributions=contributions,
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

    def parse(self, json_old):
        # context section
        inp_context = json_old.get("context")
        context = structure.Context(
            homepage=inp_context.get("homepage"),
            documentation=inp_context.get("documentation"),
            source_code=inp_context.get("sourceCode"),
            contact=inp_context.get("contact"),
            grant_number=inp_context.get("grantNo"),
        )

        # filling the spatial section
        old_spatial = json_old.get("spatial")
        spatial = structure.Spatial(
            location=old_spatial.get("location"),
            extent=old_spatial.get("extent"),
            resolution=old_spatial.get("resolution"),
        )

        # filling the temporal section
        inp_temporal = json_old["temporal"]
        temporal = structure.Temporal(
            reference_date=parse_date(inp_temporal.get("referenceDate")),
            start=parse_date(inp_temporal.get("start")),
            end=parse_date(inp_temporal.get("end")),
            resolution=inp_temporal.get("resolution"),
            ts_orientation=structure.TimestampOrientation.create(
                inp_temporal.get("timestamp")
            ),
        )

        # filling the source section
        sources = [
            structure.Source(
                title=old_source.get("title"),
                description=old_source.get("description"),
                path=old_source.get("path"),
                source_license=structure.License(
                    name=None,
                    identifier=old_source.get("license"),
                    other_references=[],
                    path=None,
                    text=None,
                ),
                source_copyright=old_source.get("copyright"),
            )
            for old_source in json_old.get("sources", [])
        ]

        # filling the license section
        licenses = [
            structure.TermsOfUse(
                lic=structure.License(
                    identifier=old_license.get("name"),
                    name=old_license.get("title"),
                    path=old_license.get("path"),
                    other_references=[],
                    text=None,
                ),
                instruction=old_license.get("instruction"),
                attribution=old_license.get("attribution"),
            )
            for old_license in json_old.get("licenses")
        ]

        # filling the contributers section
        contributors = [
            structure.Contribution(
                contributor=structure.Person(
                    name=old_contributor.get("title"),
                    email=old_contributor.get("email"),
                ),
                date=parse_date(old_contributor.get("date")),
                obj=old_contributor.get("object"),
                comment=old_contributor.get("comment"),
            )
            for old_contributor in json_old.get("contributors")
        ]

        # extending with script-user information

        resources = []
        for resource in json_old.get("resources", []):
            fields = [
                structure.Field(
                    name=field.get("name"),
                    description=field.get("description"),
                    field_type=field.get("type"),
                    unit=field.get("unit"),
                )
                for field in resource["schema"].get("fields", [])
            ]
            field_dict = {field.name: field for field in fields}
            foreign_keys = []
            for fk in resource["schema"].get("foreignKeys"):
                source_fields = [
                    field_dict[field_name] for field_name in fk.get("fields", [])
                ]
                referenced_fields = [
                    structure.Field(
                        name=fk_field, unit=None, field_type=None, description=None
                    )
                    for fk_field in fk["reference"].get("fields")
                ]
                referenced_resource = structure.Resource(
                    name=fk["reference"].get("resource"),
                    schema=structure.Schema(
                        fields=referenced_fields, foreign_keys=None, primary_key=None
                    ),
                    dialect=None,
                    encoding=None,
                    path=None,
                    profile=None,
                    resource_format=None,
                )
                l = list()
                print(l)
                references = [
                    structure.Reference(s, t)
                    for s, t in zip(source_fields, referenced_fields)
                ]
                foreign_keys.append(structure.ForeignKey(references=references))
            schema = structure.Schema(
                fields=fields,
                primary_key=resource["schema"].get("primaryKey"),
                foreign_keys=foreign_keys,
            )

            dialect = structure.Dialect(
                delimiter=resource["dialect"].get("delimiter"),
                decimal_separator=resource["dialect"].get("decimalSeparator"),
            )
            resources.append(
                structure.Resource(
                    profile=resource.get("profile"),
                    name=resource.get("name"),
                    path=resource.get("path"),
                    resource_format=resource.get("format"),
                    encoding=resource.get("encoding"),
                    schema=schema,
                    dialect=dialect,
                )
            )

        inp_review = json_old["review"]
        review = structure.Review(
            path=inp_review.get("path"), badge=inp_review.get("badge")
        )

        inp_comment = json_old["_comment"]
        comment = structure.MetaComment(
            metadata_info=inp_comment.get("metadata"),
            dates=inp_comment.get("dates"),
            units=inp_comment.get("units"),
            languages=inp_comment.get("languages"),
            licenses=inp_comment.get("licenses"),
            review=inp_comment.get("review"),
            none=inp_comment.get("none"),
        )

        metadata = structure.OEPMetadata(
            name=json_old.get("name"),
            title=json_old.get("title"),
            identifier=json_old.get("id"),
            description=json_old.get("description"),
            languages=json_old.get("language"),
            keywords=json_old.get("keywords"),
            publication_date=parse_date(json_old.get("publicationDate")),
            context=context,
            spatial=spatial,
            temporal=temporal,
            sources=sources,
            terms_of_use=licenses,
            contributions=contributors,
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
            "contributions",
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
            "contributions": subkeys_contributors,
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
            "contributions",
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
