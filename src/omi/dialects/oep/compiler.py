import json
from collections import OrderedDict

from omi import structure
from omi.dialects.base.compiler import Compiler


class JSONCompiler(Compiler):
    __METADATA_VERSION = "OEP-1.4.0"

    def _compile_date(self, date, format):
        if date:
            return date.strftime(format)
        else:
            return None

    def _construct_dict(self, *args, omit_none=True, **kwargs):
        """
        Accepts a list of arguments of shape (name: str, field: Compileable) and returns a dictionary that maps
        name -> self.visit(field). If `omit_none` is true, fields that are `None` are ignored.
        Parameters
        ----------
        args
        omit_none
        kwargs

        Returns
        -------

        """
        d = {field_name: self.visit(field) for field_name, field in args if (not omit_none) or (field is not None)}
        d.update(**kwargs)
        return d

    def visit_context(self, context: structure.Context, *args, **kwargs):
        result = self._construct_dict(
            ("homepage",  context.homepage),
            ("documentation",  context.documentation),
            ("sourceCode",  context.source_code),
            ("contact",  context.contact),
            ("grantNo",  context.grant_number),
        )
        if context.funding_agency is not None:
            if context.funding_agency.name is not None:
                result["fundingAgency"] = context.funding_agency.name
            if context.funding_agency.logo is not None:
                result["fundingAgencyLogo"] = context.funding_agency.logo
        if context.publisher is not None:
            result["publisherLogo"] = context.publisher.logo
        return result

    def visit_contribution(self, contribution: structure.Contribution, *args, **kwargs):
        return self._construct_dict(
            ("title",  contribution.contributor.name),
            ("email",  contribution.contributor.email),
            ("object",  contribution.object),
            ("comment", contribution.comment),
            ("date", self._compile_date(contribution.date, "%Y-%m-%d"))
        )

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return str(language)

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        return self._construct_dict(
            ("location",  spatial.location),
            ("extent",  spatial.extent),
            ("resolution",  spatial.resolution),
        )

    def visit_timestamp_orientation(
        self, tso: structure.TimestampOrientation, *args, **kwargs
    ):
        if tso == structure.TimestampOrientation.left:
            return "left"
        elif tso == structure.TimestampOrientation.middle:
            return "middle"
        elif tso == structure.TimestampOrientation.right:
            return "right"
        else:
            raise NotImplementedError

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        start = None
        end = None
        if temporal.ts_start is not None:
            start =self._compile_date( temporal.ts_start, "%Y-%m-%dT%H:%M%z")[:-2]
        if temporal.ts_end is not None:
            end =self._compile_date( temporal.ts_end, "%Y-%m-%dT%H:%M%z")[:-2]
        return self._construct_dict(
            ("referenceDate", self._compile_date(temporal.reference_date, "%Y-%m-%d")),
            timeseries=self._construct_dict(
                ("start",  start),
                ("end",  end),
                ("resolution",  temporal.ts_resolution),
                ("alignment",  temporal.ts_orientation),
                ("aggregationType",  temporal.aggregation),
            ),
        )

    def visit_source(self, source: structure.Source, *args, **kwargs):
        return self._construct_dict(
            ("title",  source.title),
            ("description",  source.description),
            ("path",  source.path),
            ("licenses", source.licenses)
        )

    def visit_license(self, lic: structure.License, *args, **kwargs):
        return self._construct_dict(
            ("name",  lic.identifier),
            ("title",  lic.name),
            ("path",  lic.path),
        )

    def visit_terms_of_use(self, terms_of_use: structure.TermsOfUse):
        license_kwargs = (
            self.visit(terms_of_use.license) if terms_of_use.license else {}
        )
        return self._construct_dict(
            ("instruction",  terms_of_use.instruction),
            ("attribution",  terms_of_use.attribution),
            **license_kwargs
        )

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        return self._construct_dict(
            ("profile",  resource.profile),
            ("name",  resource.name),
            ("path",  resource.path),
            ("format",  resource.format),
            ("encoding",  resource.encoding),
            ("schema",  resource.schema),
            ("dialect",  resource.dialect),
        )

    def visit_field(self, field: structure.Field, *args, **kwargs):
        return self._construct_dict(
            ("name",  field.name),
            ("description",  field.description),
            ("type",  field.type),
            ("unit",  field.unit),
        )

    def visit_schema(self, schema: structure.Schema, *args, **kwargs):
        return self._construct_dict(
            ("primaryKey",  schema.primary_key),
            ("foreignKeys", schema.foreign_keys),
            ("fields", schema.fields),
        )

    def visit_dialect(self, dialect: structure.Dialect, *args, **kwargs):
        return self._construct_dict(
            ("delimiter",  dialect.delimiter),
            ("decimalSeparator",  dialect.decimal_separator),
        )

    def visit_foreign_key(self, foreign_key: structure.ForeignKey, *args, **kwargs):
        if foreign_key.references:
            source_fields, target_fields, target_resources = zip(
                *map(self.visit, foreign_key.references)
            )
            target_resource = target_resources[0]

            return self._construct_dict(
                ("fields",  source_fields),
                reference=self._construct_dict(
                    ("resource",  target_resource),
                    ("fields",  target_fields),
                ),
            )
        else:
            raise Exception("Missing reference in foreign key")

    def visit_reference(self, reference: structure.Reference, *args, **kwargs):
        return (
            reference.source.name,
            reference.target.name,
            reference.target.resource.name,
        )

    def visit_review(self, review: structure.Review, *args, **kwargs):
        return self._construct_dict(("path",  review.path), badge=review.badge)

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        return self._construct_dict(
            ("metadata",  comment.metadata_info),
            ("dates",  comment.dates),
            ("units",  comment.units),
            ("languages",  comment.languages),
            ("licenses",  comment.licenses),
            ("review",  comment.review),
            ("null",  comment.none),
        )

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        publication_date = None
        if metadata.publication_date is not None:
            publication_date =self._compile_date( metadata.publication_date, "%Y-%m-%d")
        return self._construct_dict(
            ("name",  metadata.name),
            ("title",  metadata.title),
            ("id",  metadata.identifier),
            ("description",  metadata.description),
            ("keywords",  metadata.keywords),
            ("publicationDate",  publication_date),
            ("context",  metadata.context),
            ("spatial",  metadata.spatial),
            ("temporal",  metadata.temporal),
            ("review", metadata.review),
            ("_comment", metadata.comment),
            ("language", metadata.languages),
            ("sources", metadata.sources),
            ("licenses", metadata.license),
            ("contributors", metadata.contributions),
            ("resources", metadata.resources),
            metaMetadata=self._construct_dict(
                ("metadataVersion",  self.__METADATA_VERSION),
                metadataLicense=self._construct_dict(
                    name="CC0-1.0",
                    title="Creative Commons Zero v1.0 Universal",
                    path="https://creativecommons.org/publicdomain/zero/1.0/",
                ),
            ),
        )
