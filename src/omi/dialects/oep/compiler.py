import json
from collections import OrderedDict

from omi import structure
from omi.dialects.base.compiler import Compiler


class JSONCompiler(Compiler):
    __METADATA_VERSION = "OEP-1.4"

    def visit_context(self, context: structure.Context, *args, **kwargs):
        return OrderedDict(
            homepage=self.visit(context.homepage),
            documentation=self.visit(context.documentation),
            sourceCode=self.visit(context.source_code),
            contact=self.visit(context.contact),
            grantNo=self.visit(context.grant_number),
        )

    def visit_contribution(self, contribution: structure.Contribution, *args, **kwargs):
        return OrderedDict(
            title=self.visit(contribution.contributor.name),
            email=self.visit(contribution.contributor.email),
            object=self.visit(contribution.object),
            date=contribution.date.strftime("%Y-%m-%d"),
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
        return OrderedDict(
            referenceDate=temporal.reference_date.strftime("%Y-%m-%d"),
            start=temporal.ts_start.strftime("%Y-%m-%dT%H:%M%z")[:-2],
            end=temporal.ts_end.strftime("%Y-%m-%dT%H:%M%z")[:-2],
            resolution=self.visit(temporal.ts_resolution),
            timestamp=self.visit(temporal.ts_orientation),
        )

    def visit_source(self, source: structure.Source, *args, **kwargs):
        return OrderedDict(
            title=self.visit(source.title),
            description=self.visit(source.description),
            path=self.visit(source.path),
            license=self.visit(source.license.identifier),
            copyright=self.visit(source.copyright),
        )

    def visit_license(self, lic: structure.License, *args, **kwargs):
        return OrderedDict(
            name=self.visit(lic.identifier),
            title=self.visit(lic.name),
            path=self.visit(lic.path),
        )

    def visit_terms_of_use(self, terms_of_use: structure.TermsOfUse):
        return OrderedDict(
            instruction=self.visit(terms_of_use.instruction),
            attribution=self.visit(terms_of_use.attribution),
            **self.visit(terms_of_use.license)
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
            foreignKeys=list(map(self.visit, schema.foreign_keys)),
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
            none=comment.none,
        )

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        return OrderedDict(
            name=metadata.name,
            title=metadata.title,
            id=metadata.identifier,
            description=metadata.description,
            language=list(map(self.visit, metadata.languages)),
            keywords=metadata.keywords,
            publicationDate=metadata.publication_date.strftime("%Y-%m-%d"),
            context=self.visit(metadata.context),
            spatial=self.visit(metadata.spatial),
            temporal=self.visit(metadata.temporal),
            sources=list(map(self.visit, metadata.sources)),
            licenses=list(map(self.visit, metadata.license)),
            contributors=list(map(self.visit, metadata.contributions)),
            resources=list(map(self.visit, metadata.resources)),
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
