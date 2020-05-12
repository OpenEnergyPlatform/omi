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

    def visit_context(self, context: structure.Context, *args, **kwargs):
        result = OrderedDict(
            homepage=self.visit(context.homepage),
            documentation=self.visit(context.documentation),
            sourceCode=self.visit(context.source_code),
            contact=self.visit(context.contact),
            grantNo=self.visit(context.grant_number),
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
        return OrderedDict(
            title=self.visit(contribution.contributor.name),
            email=self.visit(contribution.contributor.email),
            object=self.visit(contribution.object),
            date=self._compile_date(contribution.date, "%Y-%m-%d")
            if contribution.date is not None
            else None,
            comment=self.visit(contribution.comment),
        )

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return str(language)

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        return OrderedDict(
            location=self.visit(spatial.location),
            extent=self.visit(spatial.extent),
            resolution=self.visit(spatial.resolution),
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
        return OrderedDict(
            referenceDate=self._compile_date(temporal.reference_date, "%Y-%m-%d"),
            timeseries=OrderedDict(
                start=start,
                end=end,
                resolution=self.visit(temporal.ts_resolution),
                alignment=self.visit(temporal.ts_orientation),
                aggregationType=self.visit(temporal.aggregation),
            ),
        )

    def visit_source(self, source: structure.Source, *args, **kwargs):
        return OrderedDict(
            title=self.visit(source.title),
            description=self.visit(source.description),
            path=self.visit(source.path),
            licenses=[self.visit(l) for l in source.licenses]
            if source.licenses is not None
            else None,
        )

    def visit_license(self, lic: structure.License, *args, **kwargs):
        return OrderedDict(
            name=self.visit(lic.identifier),
            title=self.visit(lic.name),
            path=self.visit(lic.path),
        )

    def visit_terms_of_use(self, terms_of_use: structure.TermsOfUse):
        license_kwargs = (
            self.visit(terms_of_use.license) if terms_of_use.license else {}
        )
        return OrderedDict(
            instruction=self.visit(terms_of_use.instruction),
            attribution=self.visit(terms_of_use.attribution),
            **license_kwargs
        )

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        return OrderedDict(
            profile=self.visit(resource.profile),
            name=self.visit(resource.name),
            path=self.visit(resource.path),
            format=self.visit(resource.format),
            encoding=self.visit(resource.encoding),
            schema=self.visit(resource.schema),
            dialect=self.visit(resource.dialect),
        )

    def visit_field(self, field: structure.Field, *args, **kwargs):
        return OrderedDict(
            name=field.name,
            description=field.description,
            type=field.type,
            unit=field.unit,
        )

    def visit_schema(self, schema: structure.Schema, *args, **kwargs):
        return OrderedDict(
            fields=list(map(self.visit, schema.fields)),
            primaryKey=self.visit(schema.primary_key),
            foreignKeys=list(map(self.visit, schema.foreign_keys))
            if schema.foreign_keys
            else None,
        )

    def visit_dialect(self, dialect: structure.Dialect, *args, **kwargs):
        return OrderedDict(
            delimiter=self.visit(dialect.delimiter),
            decimalSeparator=self.visit(dialect.decimal_separator),
        )

    def visit_foreign_key(self, foreign_key: structure.ForeignKey, *args, **kwargs):
        if foreign_key.references:
            source_fields, target_fields, target_resources = zip(
                *map(self.visit, foreign_key.references)
            )

            target_resource = target_resources[0]

            return OrderedDict(
                fields=source_fields,
                reference=OrderedDict(
                    resource=self.visit(target_resource),
                    fields=self.visit(target_fields),
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
        return OrderedDict(path=review.path, badge=review.badge)

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        return OrderedDict(
            metadata=comment.metadata_info,
            dates=comment.dates,
            units=comment.units,
            languages=comment.languages,
            licenses=comment.licenses,
            review=comment.review,
            null=comment.none,
        )

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        publication_date = None
        if metadata.publication_date is not None:
            publication_date =self._compile_date( metadata.publication_date, "%Y-%m-%d")
        return OrderedDict(
            name=metadata.name,
            title=metadata.title,
            id=metadata.identifier,
            description=metadata.description,
            language=list(map(self.visit, metadata.languages))
            if metadata.languages is not None
            else None,
            keywords=metadata.keywords,
            publicationDate=publication_date,
            context=self.visit(metadata.context),
            spatial=self.visit(metadata.spatial),
            temporal=self.visit(metadata.temporal),
            sources=list(map(self.visit, metadata.sources))
            if metadata.sources is not None
            else None,
            licenses=list(map(self.visit, metadata.license))
            if metadata.license is not None
            else None,
            contributors=list(map(self.visit, metadata.contributions))
            if metadata.contributions is not None
            else None,
            resources=list(map(self.visit, metadata.resources))
            if metadata.resources is not None
            else None,
            review=self.visit(metadata.review),
            metaMetadata=OrderedDict(
                metadataVersion=self.__METADATA_VERSION,
                metadataLicense=OrderedDict(
                    name="CC0-1.0",
                    title="Creative Commons Zero v1.0 Universal",
                    path="https://creativecommons.org/publicdomain/zero/1.0/",
                ),
            ),
            _comment=self.visit(metadata.comment),
        )
