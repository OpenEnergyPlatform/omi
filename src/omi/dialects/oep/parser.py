#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import pkg_resources
from dateutil.parser import parse as parse_date
from jsonschema import ValidationError
from jsonschema import validate

from omi import structure
from omi.dialects.base.parser import Parser
from omi.dialects.base.parser import ParserException


def parse_date_or_none(x, *args, **kwargs):
    if x is None:
        return None
    else:
        return parse_date(x, *args, **kwargs)


class JSONParser(Parser):
    _schema_file = None

    def __init__(self, **kwargs):
        resource_package = __name__
        # Do not use os.path.join()
        resource_path = self._schema_file
        schema_str = pkg_resources.resource_string(resource_package, resource_path)
        if isinstance(schema_str, bytes):
            schema_str = schema_str.decode("utf-8")
        self.schema = json.loads(schema_str)

    def load_string(self, string: str, *args, **kwargs):
        return json.loads(string)

    def validate(self, jsn: dict):
        """
        Check whether the given dictionary adheres to the the json-schema
        specification

        Parameters
        ----------
        jsn
          The dictionary to validate

        Returns
        -------
          Nothing

        """
        validate(jsn, self.schema)

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
            jsn = json.loads(inp)
        except ValueError:
            return False
        else:
            try:
                self.validate(jsn)
            except ValidationError:
                return False
            else:
                return True


class JSONParser_1_3(JSONParser):
    _schema_file = "spec/metadata/v130/schema.json"

    def parse(self, json_old, *args, **kwargs):

        self.validate(json_old)

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
                    # source_copyright=old_source.get("copyright"),
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
    _schema_file = "spec/metadata/v140/schema.json"

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

        self.validate(json_old)

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
                    else None,
                    aggregation=inp_timeseries.get("aggregationType"),
                )
            temporal = structure.Temporal(
                reference_date=parse_date_or_none(inp_temporal.get("referenceDate")),
                **timeseries
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
        else:
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
                    old_foreign_keys = old_schema.get("foreignKeys")
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
