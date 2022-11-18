#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import pathlib

import jsonschema
from dateutil.parser import parse as parse_date
from jsonschema import ValidationError
# oemetadata
from metadata.latest.schema import OEMETADATA_LATEST_SCHEMA
from metadata.v130.schema import OEMETADATA_V130_SCHEMA
from metadata.v140.schema import OEMETADATA_V140_SCHEMA
from metadata.v141.schema import OEMETADATA_V141_SCHEMA
from metadata.v150.schema import OEMETADATA_V150_SCHEMA
from metadata.v151.schema import OEMETADATA_V151_SCHEMA

from omi import structure
from omi.dialects.base.parser import Parser
from omi.dialects.base.parser import ParserException
from omi.oem_structures import oem_v15

ALL_OEM_SCHEMAS = [
    OEMETADATA_LATEST_SCHEMA,
    OEMETADATA_V150_SCHEMA,
    OEMETADATA_V141_SCHEMA,
    OEMETADATA_V140_SCHEMA,
    OEMETADATA_V130_SCHEMA,
]


def parse_date_or_none(x, *args, **kwargs):
    if x is None:
        return None
    else:
        return parse_date(x, *args, **kwargs)


def create_report_json(
    error_data: list[dict],
    save_at: pathlib.Path = "reports/",
    filename: str = "report.json",
):
    # if len(error_data) >= 1:
    pathlib.Path(save_at).mkdir(parents=True, exist_ok=True)
    with open(f"{save_at}{filename}", "w", encoding="utf-8") as fp:
        json.dump(error_data, fp, indent=4, sort_keys=False)

    print(
        f"Created error report containing {len(error_data)} errors at: {save_at}{filename}"
    )


class JSONParser(Parser):
    # one_schema_was_valid = False

    def load_string(self, string: str, *args, **kwargs):
        return json.loads(string)

    def get_json_validator(self, schema: OEMETADATA_LATEST_SCHEMA):
        """
        Get the jsonschema validator that matches the schema.
        Also checks if the schmea is valid.

        Args:
            schema (OEMETADATA_LATEST_SCHEMA):

        Returns:
            validator: jsonschema.Draft202012Validator
        """
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema=schema)
        return validator

    def get_any_schema_valid(
        self,
        metadata: dict,
        schemas: list = ALL_OEM_SCHEMAS,
    ):
        """
        Additional helper funtion - get any schema that is valid for the metadata.
        Returns The first valid schema or None

        Args:
            schemas (list): _description_
            metadata (dict): _description_

        Returns:
            _type_: _description_
        """

        valid_schemas = []
        for schema in schemas:
            if len(valid_schemas) <= 1:
                continue
            elif self.is_valid(inp=metadata, schema=schema):
                valid_schemas.append(schema)

        if len(valid_schemas) >= 1:
            valid_schemas = None
        return valid_schemas

    def get_schema_by_metadata_version(self, metadata: dict):
        oem_13 = ["1.3", "OEP-1.3"]
        oem_14 = "OEP-1.4.0"
        oem_141 = "OEP-1.4.1"
        oem_15 = "OEP-1.5.0"
        oem_151 = "OEP-1.5.1"

        schema = None

        if metadata.get("metadata_version"):
            if metadata.get("metadata_version") in oem_13:
                schema = OEMETADATA_V130_SCHEMA

        if metadata.get("metaMetadata"):
            if metadata.get("metaMetadata")["metadataVersion"] == oem_14:
                schema = OEMETADATA_V140_SCHEMA
            if metadata.get("metaMetadata")["metadataVersion"] == oem_141:
                schema = OEMETADATA_V141_SCHEMA
            if metadata.get("metaMetadata")["metadataVersion"] == oem_15:
                schema = OEMETADATA_V150_SCHEMA
            if metadata.get("metaMetadata")["metadataVersion"] == oem_151:
                schema = OEMETADATA_V151_SCHEMA

        # fallback to latest schema if metadata does not contian the exprected metadata version sting
        if schema is None:
            logging.info(
                "Metadata does not contain the expected 'metaMetadata' or 'metadata_version' key. Fallback to latest schema."
            )
            schema = OEMETADATA_LATEST_SCHEMA

        print(schema.get("$id"))

        return schema

    def validate(self, metadata: dict, schema: dict = None):
        """
        Check whether the given dictionary adheres to the the json-schema
        and oemetadata specification. If errors are found a jsonschema error
        report is created in directory 'reports/'.

        Parameters
        ----------
        metadata
          The dictionary to validate
        schema: optional
          The jsonschema used for validation.
          Default is None.
        Returns
        -------
          Nothing
        """

        report = []
        if not schema:
            schema = self.get_schema_by_metadata_version(metadata=metadata)
        validator = self.get_json_validator(schema)

        for error in sorted(validator.iter_errors(instance=metadata), key=str):
            # https://python-jsonschema.readthedocs.io/en/stable/errors/#handling-validation-errors
            error_dict = {
                "oemetadata schema version": schema.get("$id"),
                "json path": error.absolute_path,
                "instance path": [i for i in error.absolute_path],
                "value that raised the error": error.instance,
                "error message": error.message,
                "schema_path": [i for i in error.schema_path],
            }
            report.append(error_dict)

        create_report_json(report)

    def is_valid(self, inp: dict, schema):

        # 1 - valid JSON?
        if isinstance(inp, str):
            try:
                jsn = json.loads(inp, encode="utf-8")
            except ValueError:
                return False
        else:
            jsn = inp

        # 2 - valid OEMETADATA
        try:
            validator = self.get_json_validator(schema)
            validator.validate(jsn)
            return True
        except ValidationError:
            return False


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
        context = None

        # filling the spatial section
        if "spatial" in json_old:
            old_spatial = json_old.get("spatial")
            spatial = structure.Spatial(
                extent=old_spatial.get("extent"),
                resolution=old_spatial.get("resolution"),
            )
        else:
            spatial = None

        # filling the temporal section
        old_temporal = json_old.get("temporal")
        if old_temporal is None:
            temporal = None
        else:
            temporal = structure.Temporal(
                reference_date=parse_date_or_none(old_temporal.get("reference_date"))
            )

        # filling the source section
        # For future reference: There is an important semantic difference between `source = None` and `sources = []`
        # The former means that there is no information regarding sources the latter means that there are no sources.
        # This is holds for all lists around here
        old_sources = json_old.get("sources")
        if old_sources is None:
            sources = None
        else:
            sources = [
                structure.Source(
                    title=old_source.get("name"),
                    description=old_source.get("description"),
                    path=old_source.get("url"),
                    licenses=[
                        structure.TermsOfUse(attribution=old_source.get("copyright"))
                    ],
                )
                for old_source in old_sources
            ]

        # filling the license section
        old_license = json_old.get("license")
        if old_license is None:
            licenses = None  # not []! (see sources)
        else:
            licenses = [
                structure.TermsOfUse(
                    lic=structure.License(
                        identifier=old_license.get("id"),
                        name=old_license.get("name"),
                        path=old_license.get("url"),
                    ),
                    instruction=old_license.get("instruction"),
                    attribution=old_license.get("copyright"),
                )
            ]

        # filling the contributers section
        old_contributors = json_old.get("contributors")
        if old_contributors is None:
            contributions = None
        else:
            contributions = [
                structure.Contribution(
                    contributor=structure.Person(
                        name=old_contributor.get("name"),
                        email=old_contributor.get("email"),
                    ),
                    date=parse_date_or_none(old_contributor.get("date")),
                    comment=old_contributor.get("comment"),
                )
                for old_contributor in old_contributors
            ]

        # extending with script-user information

        old_resources = json_old.get("resources")
        if old_resources is None:
            resources = None
        else:
            resources = []
            if len(old_resources) == 0:
                raise ParserException("Resource field doesn't have any child entity")
            for resource in old_resources:
                old_fields = resource.get("fields")
                if old_fields is None:
                    fields = None
                else:
                    fields = [
                        structure.Field(
                            name=field.get("name"),
                            description=field.get("description"),
                            unit=field.get("unit"),
                        )
                        for field in old_fields
                    ]
                schema = structure.Schema(fields=fields)
                resources.append(
                    structure.Resource(
                        name=resource.get("name"),
                        resource_format="PostgreSQL",
                        schema=schema,
                    )
                )

        review = None

        comment = None

        metadata = structure.OEPMetadata(
            title=json_old.get("title"),
            description=json_old.get("description"),
            languages=json_old.get("language"),
            identifier=None,
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

    def parse_term_of_use(self, old_license: dict):
        return structure.TermsOfUse(
            lic=structure.License(
                identifier=old_license.get("name"),
                name=old_license.get("title"),
                path=old_license.get("path"),
            ),
            instruction=old_license.get("instruction"),
            attribution=old_license.get("attribution"),
        )

    def parse(self, json_old: dict, *args, **kwargs):
        # context section
        if "id" not in json_old:
            raise ParserException("metadata string does not contain an id")

        inp_context = json_old.get("context")
        if inp_context is None:
            context = None
        else:

            funding_agency = None
            if "fundingAgency" in inp_context:
                funding_agency = structure.Agency(
                    name=inp_context.get("fundingAgency"),
                    logo=inp_context.get("fundingAgencyLogo"),
                )

            context = structure.Context(
                homepage=inp_context.get("homepage"),
                documentation=inp_context.get("documentation"),
                source_code=inp_context.get("sourceCode"),
                contact=inp_context.get("contact"),
                grant_number=inp_context.get("grantNo"),
                funding_agency=funding_agency,
                publisher=structure.Agency(logo=inp_context.get("publisherLogo"))
                if "publisherLogo" in inp_context
                else None,
            )

        # filling the spatial section
        old_spatial = json_old.get("spatial")
        if old_spatial is None:
            spatial = None
        else:
            spatial = structure.Spatial(
                location=old_spatial.get("location"),
                extent=old_spatial.get("extent"),
                resolution=old_spatial.get("resolution"),
            )

        # filling the temporal section
        inp_temporal = json_old.get("temporal")
        if inp_temporal is None:
            temporal = None
        else:
            inp_timeseries = inp_temporal.get("timeseries")
            timeseries = {}
            if inp_timeseries is not None:
                timeseries = dict(
                    start=parse_date_or_none(inp_timeseries.get("start")),
                    end=parse_date_or_none(inp_timeseries.get("end")),
                    resolution=inp_timeseries.get("resolution"),
                    ts_orientation=structure.TimestampOrientation.create(
                        inp_timeseries.get("alignment")
                    )
                    if "alignment" in inp_timeseries
                    and inp_timeseries["alignment"] is not None
                    else None,
                    aggregation=inp_timeseries.get("aggregationType"),
                )
            temporal = structure.Temporal(
                reference_date=parse_date_or_none(inp_temporal.get("referenceDate")),
                **timeseries,
            )

        # filling the source section
        old_sources = json_old.get("sources")
        if old_sources is None:
            sources = None
        else:
            sources = [
                structure.Source(
                    title=old_source.get("title"),
                    description=old_source.get("description"),
                    path=old_source.get("path"),
                    licenses=[
                        self.parse_term_of_use(l)
                        for l in old_source.get("licenses", [])
                    ],
                )
                for old_source in old_sources
            ]

        # filling the license section
        old_licenses = json_old.get("licenses")
        if old_licenses is None:
            licenses = None
        else:
            licenses = [
                self.parse_term_of_use(old_license) for old_license in old_licenses
            ]

        # filling the contributers section
        old_contributors = json_old.get("contributors")
        if old_contributors is None:
            contributors = None
        else:
            contributors = [
                structure.Contribution(
                    contributor=structure.Person(
                        name=old_contributor.get("title"),
                        email=old_contributor.get("email"),
                    ),
                    date=parse_date_or_none(old_contributor.get("date")),
                    obj=old_contributor.get("object"),
                    comment=old_contributor.get("comment"),
                )
                for old_contributor in old_contributors
            ]

        # extending with script-user information
        old_resources = json_old.get("resources")
        if old_resources is None:
            resources = None
        # Code added to raise exception when resource is empty
        else:
            if len(old_resources) == 0:
                raise ParserException("Resource field doesn't have any child entity")
            resources = []
            for resource in old_resources:
                old_schema = resource.get("schema")
                if old_schema is None:
                    schema = None
                else:
                    old_fields = old_schema.get("fields")
                    if old_fields is None:
                        fields = None
                    else:
                        fields = [
                            structure.Field(
                                name=field.get("name"),
                                description=field.get("description"),
                                field_type=field.get("type"),
                                unit=field.get("unit"),
                            )
                            for field in old_fields
                        ]
                    field_dict = {field.name: field for field in fields or []}
                    old_foreign_keys = old_schema.get("foreignKeys", [])
                    foreign_keys = []
                    for fk in old_foreign_keys:
                        old_reference = fk.get("reference")
                        if old_reference is None:
                            raise ParserException("Foreign key without reference:", fk)
                        source_fields = [
                            field_dict[field_name]
                            for field_name in fk.get("fields", [])
                        ]
                        old_referenced_fields = old_reference.get("fields")
                        if old_referenced_fields is None:
                            referenced_fields = None
                        else:
                            referenced_fields = [
                                structure.Field(name=fk_field)
                                for fk_field in old_referenced_fields
                            ]
                        referenced_resource = structure.Resource(
                            name=old_reference.get("resource"),
                            schema=structure.Schema(fields=referenced_fields),
                        )
                        for rf in referenced_fields:
                            rf.resource = referenced_resource
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
                old_dialect = resource.get("dialect")
                if old_dialect is None:
                    dialect = None
                else:
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

        inp_review = json_old.get("review")
        if inp_review is None:
            review = None
        else:
            review = structure.Review(
                path=inp_review.get("path"), badge=inp_review.get("badge")
            )

        inp_comment = json_old.get("_comment")
        if inp_comment is None:
            comment = None
        else:
            comment = structure.MetaComment(
                metadata_info=inp_comment.get("metadata"),
                dates=inp_comment.get("dates"),
                units=inp_comment.get("units"),
                languages=inp_comment.get("languages"),
                licenses=inp_comment.get("licenses"),
                review=inp_comment.get("review"),
                none=inp_comment.get("null"),
            )

        metadata = structure.OEPMetadata(
            name=json_old.get("name"),
            title=json_old.get("title"),
            identifier=json_old["id"],
            description=json_old.get("description"),
            languages=json_old.get("language"),
            keywords=json_old.get("keywords"),
            publication_date=parse_date_or_none(json_old.get("publicationDate")),
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


# TODO: Update parser below


class JSONParser_1_5(JSONParser):
    def parse_from_string(
        self,
        string: str,
        load_args=None,
        parse_args=None,
        load_kwargs=None,
        parse_kwargs=None,
    ) -> oem_v15.OEPMetadata:
        """
        Parse a string into :class:`~omi.oem_structures.oem_v15.OEPMetadata`

        Parameters
        ----------
        string

        Returns
        -------

        """
        return self.parse(
            self.load_string(string, *(load_args or []), **(load_kwargs or {})),
            *(parse_args or []),
            **(parse_kwargs or {}),
        )

    def parse_term_of_use(self, old_license: dict):
        return oem_v15.TermsOfUse(
            lic=oem_v15.License(
                identifier=old_license.get("name"),
                name=old_license.get("title"),
                path=old_license.get("path"),
            ),
            instruction=old_license.get("instruction"),
            attribution=old_license.get("attribution"),
        )

    def parse_timeseries(self, old_timeseries: dict):
        pass

    def parse(self, json_old: dict, *args, **kwargs):
        """_summary_

        Args:
            json_old (dict): _description_

        Raises:
            ParserException: _description_
            ParserException: _description_
            ParserException: _description_

        Returns:
            _type_: _description_
        """

        if "id" not in json_old:
            raise ParserException("metadata string does not contain an id")

        # filling the subject section
        old_subjects = json_old.get("subject")
        if old_subjects is None:
            subject = None
        else:
            subject = [
                oem_v15.Subject(
                    name=old_subject.get("name"), path=old_subject.get("path")
                )
                for old_subject in old_subjects
            ]

        # context section
        inp_context: dict = json_old.get("context")
        if inp_context is None:
            context = None
        else:

            funding_agency = None
            if "fundingAgency" in inp_context:
                funding_agency = oem_v15.Agency(
                    name=inp_context.get("fundingAgency"),
                    logo=inp_context.get("fundingAgencyLogo"),
                )

            context = oem_v15.Context(
                homepage=inp_context.get("homepage"),
                documentation=inp_context.get("documentation"),
                source_code=inp_context.get("sourceCode"),
                contact=inp_context.get("contact"),
                grant_number=inp_context.get("grantNo"),
                funding_agency=funding_agency,
                publisher=oem_v15.Agency(logo=inp_context.get("publisherLogo"))
                if "publisherLogo" in inp_context
                else None,
            )

        # filling the spatial section
        old_spatial: dict = json_old.get("spatial")
        if old_spatial is None:
            spatial = None
        else:
            spatial = oem_v15.Spatial(
                location=old_spatial.get("location"),
                extent=old_spatial.get("extent"),
                resolution=old_spatial.get("resolution"),
            )

        # filling the temporal section
        inp_temporal: dict = json_old.get("temporal")
        if inp_temporal is None:
            temporal = None
        else:
            inp_timeseries: dict = inp_temporal.get("timeseries", [])
            if inp_timeseries is None:
                timeseries = None
            else:
                timeseries = [
                    oem_v15.Timeseries(
                        start=parse_date_or_none(ts.get("start")),
                        end=parse_date_or_none(ts.get("end")),
                        resolution=ts.get("resolution"),
                        ts_orientation=oem_v15.TimestampOrientation.create(
                            ts.get("alignment")
                        )
                        if "alignment" in ts and ts["alignment"] is not None
                        else None,
                        aggregation=ts.get("aggregationType"),
                    )
                    for ts in inp_timeseries
                ]
            temporal = oem_v15.Temporal(
                reference_date=parse_date_or_none(inp_temporal.get("referenceDate")),
                # TODO: does ** kwargs work on list?
                timeseries_collection=timeseries,
            )

        # filling the source section
        old_sources = json_old.get("sources")
        if old_sources is None:
            sources = None
        else:
            sources = [
                oem_v15.Source(
                    title=old_source.get("title"),
                    description=old_source.get("description"),
                    path=old_source.get("path"),
                    licenses=[
                        self.parse_term_of_use(l)
                        for l in old_source.get("licenses", [])
                    ],
                )
                for old_source in old_sources
            ]

        # filling the license section
        old_licenses = json_old.get("licenses")
        if old_licenses is None:
            licenses = None
        else:
            licenses = [
                self.parse_term_of_use(old_license) for old_license in old_licenses
            ]

        # filling the contributers section
        old_contributors = json_old.get("contributors")
        if old_contributors is None:
            contributors = None
        else:
            contributors = [
                oem_v15.Contribution(
                    contributor=oem_v15.Person(
                        name=old_contributor.get("title"),
                        email=old_contributor.get("email"),
                    ),
                    date=parse_date_or_none(old_contributor.get("date")),
                    obj=old_contributor.get("object"),
                    comment=old_contributor.get("comment"),
                )
                for old_contributor in old_contributors
            ]

        # extending with script-user information
        old_resources = json_old.get("resources")
        if old_resources is None:
            resources = None
        # Code added to raise exception when resource is empty
        else:
            if len(old_resources) == 0:
                raise ParserException("Resource field doesn't have any child entity")
            resources = []
            for resource in old_resources:
                old_schema = resource.get("schema")
                if old_schema is None:
                    schema = None
                else:
                    # filling the fields section
                    old_fields = old_schema.get("fields")
                    if old_fields is None:
                        fields = None
                    else:
                        fields = []

                        for field in old_fields:
                            # filling the is about section
                            old_is_abouts = field.get("isAbout")
                            if old_is_abouts is None:
                                isAbout = None
                            else:
                                isAbout = [
                                    oem_v15.IsAbout(
                                        name=old_is_about.get("name"),
                                        path=old_is_about.get("path"),
                                    )
                                    for old_is_about in old_is_abouts
                                ]

                            # filling the value reference section
                            old_value_references = field.get("valueReference")
                            if old_value_references is None:
                                valueReference = None
                            else:
                                valueReference = [
                                    oem_v15.ValueReference(
                                        value=old_value_reference.get("value"),
                                        name=old_value_reference.get("name"),
                                        path=old_value_reference.get("path"),
                                    )
                                    for old_value_reference in old_value_references
                                ]

                            fields.append(
                                oem_v15.Field(
                                    name=field.get("name"),
                                    description=field.get("description"),
                                    field_type=field.get("type"),
                                    isAbout=isAbout,
                                    valueReference=valueReference,
                                    unit=field.get("unit"),
                                )
                            )

                    field_dict = {field.name: field for field in fields or []}
                    old_foreign_keys = old_schema.get("foreignKeys", [])
                    foreign_keys = []
                    for fk in old_foreign_keys:
                        old_reference = fk.get("reference")
                        if old_reference is None:
                            raise ParserException("Foreign key without reference:", fk)
                        source_fields = [
                            field_dict[field_name]
                            for field_name in fk.get("fields", [])
                        ]
                        old_referenced_fields = old_reference.get("fields")
                        if old_referenced_fields is None:
                            referenced_fields = None
                        else:
                            referenced_fields = [
                                oem_v15.Field(name=fk_field)
                                for fk_field in old_referenced_fields
                            ]
                        referenced_resource = oem_v15.Resource(
                            name=old_reference.get("resource"),
                            schema=oem_v15.Schema(fields=referenced_fields),
                        )
                        for rf in referenced_fields:
                            rf.resource = referenced_resource
                        references = [
                            oem_v15.Reference(s, t)
                            for s, t in zip(source_fields, referenced_fields)
                        ]
                        foreign_keys.append(oem_v15.ForeignKey(references=references))
                    schema = oem_v15.Schema(
                        fields=fields,
                        primary_key=resource["schema"].get("primaryKey"),
                        foreign_keys=foreign_keys,
                    )
                old_dialect = resource.get("dialect")
                if old_dialect is None:
                    dialect = None
                else:
                    dialect = oem_v15.Dialect(
                        delimiter=resource["dialect"].get("delimiter"),
                        decimal_separator=resource["dialect"].get("decimalSeparator"),
                    )
                resources.append(
                    oem_v15.Resource(
                        profile=resource.get("profile"),
                        name=resource.get("name"),
                        path=resource.get("path"),
                        resource_format=resource.get("format"),
                        encoding=resource.get("encoding"),
                        schema=schema,
                        dialect=dialect,
                    )
                )

        inp_review = json_old.get("review")
        if inp_review is None:
            review = None
        else:
            review = oem_v15.Review(
                path=inp_review.get("path"), badge=inp_review.get("badge")
            )

        inp_comment = json_old.get("_comment")
        if inp_comment is None:
            comment = None
        else:
            comment = oem_v15.MetaComment(
                metadata_info=inp_comment.get("metadata"),
                dates=inp_comment.get("dates"),
                units=inp_comment.get("units"),
                languages=inp_comment.get("languages"),
                licenses=inp_comment.get("licenses"),
                review=inp_comment.get("review"),
                null=inp_comment.get("null"),
                todo=inp_comment.get("todo"),
            )

        metadata = oem_v15.OEPMetadata(
            name=json_old.get("name"),
            title=json_old.get("title"),
            identifier=json_old["id"],
            description=json_old.get("description"),
            subject=subject,
            languages=json_old.get("language"),
            keywords=json_old.get("keywords"),
            publication_date=parse_date_or_none(json_old.get("publicationDate")),
            context=context,
            spatial=spatial,
            temporal=temporal,
            sources=sources,
            terms_of_use=licenses,
            contributions=contributors,
            resources=resources,
            databus_identifier=json_old.get("@id"),
            databus_context=json_old.get("@context"),
            review=review,
            comment=comment,
        )
        return metadata

    def assert_1_5_metastring(self, json_string: str):
        """Checks string conformity to OEP Metadata Standard Version 1.5

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
        subkeys_timeseries = [
            "start",
            "end",
            "resolution",
            "alignment",
            "aggregationType",
        ]
        subkeys_temporal = ["reference_date", "timeseries"]
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
