from metadata_tool import structure
from metadata_tool.dialects.base.compiler import Compiler


class JSONCompiler(Compiler):

    def visit_context(self, context: structure.Context):
        return dict(
            homepage=self.visit(context.homepage),
            documentation=self.visit(context.documentation),
            sourceCode=self.visit(context.source_code),
            contact=self.visit(context.contact),
            grantNo=self.visit(context.grant_number)
        )

    def visit_contributor(self, contributor: structure.Contributor):
        return dict(
            name=self.visit(contributor.name),
            email=self.visit(contributor.email),
            date=self.visit(contributor.date),
            comment=self.visit(contributor.comment)
        )

    def visit_language(self, language: structure.Language):
        return str(language)

    def visit_spatial(self, spatial: structure.Spatial):
        return dict(
            location=self.visit(spatial.location),
            extend=self.visit(spatial.extend),
            resolution=self.visit(spatial.resolution)
        )

    def visit_temporal(self, temporal: structure.Temporal):
        return dict(
            reference_date=self.visit(temporal.reference_date),
            ts_start=self.visit(temporal.ts_start),
            ts_end=self.visit(temporal.ts_end),
            ts_resolution=self.visit(temporal.ts_resolution)
        )

    def visit_source(self, source: structure.Source):
        return dict(
            title=self.visit(source.title),
            description=self.visit(source.description),
            path=self.visit(source.path),
            license=self.visit(source.license.name),
            copyright=self.visit(source.copyright))

    def visit_license(self, lic: structure.License):
        return dict(
            name=self.visit(lic.name),
            title=self.visit(lic.title),
            path=self.visit(lic.path),
            instruction=self.visit(lic.instruction),
            attribution=self.visit(lic.attribution))

    def visit_resource(self, resource: structure.Resource):
        return dict(
            profile=self.visit(resource.profile),
            name=self.visit(resource.name),
            path=self.visit(resource.path),
            format=self.visit(resource.name),
            encoding=self.visit(resource.encoding),
            schema=self.visit(resource.schema))

    def visit_field(self, field: structure.Field):
        return dict(
            name=field.name,
            description=field.description,
            type=field.type,
            unit=field.unit
        )

    def visit_schema(self, schema: structure.Schema):
        return dict(
            fields = list(map(self.visit, schema.fields)),
            primaryKey = self.visit(schema.primary_key),
            foreignKeys = list(map(self.visit, schema.foreign_keys)))

    def visit_foreign_key(self, foreign_key: structure.ForeignKey):
        return dict(
            fields=self.visit(foreign_key.fields),
            reference=self.visit(foreign_key.reference)
        )

    def visit_reference(self, reference: structure.Reference):
        return dict(
            resource=self.visit(reference.resource),
            fields=self.visit(reference.fields)
        )

    def visit_review(self, review: structure.Review):
        return dict(
            path=review.path,
            badge=review.badge
        )

    def visit_meta_meta_data(self, metadata: structure.MetaMetaData):
        return dict(
            metadataVersion=metadata.version,
            metadataLicense=dict(
                name=metadata.license.name,
                title=metadata.license.title,
                path=metadata.license.path
            )
        )

    def visit_meta_comment(self, comment: structure.MetaComment):
        return dict(
            metadata=comment.metadata_info,
            dates=comment.dates,
            units=comment.units,
            languages=comment.languages,
            licenses=comment.licenses,
            review=comment.review,
            none=comment.none,
        )

    def visit_metadata(self, metadata: structure.OEPMetadata):
        return dict(
            title=metadata.title,
            identifier=metadata.identifier,
            description=metadata.description,
            language=list(map(self.visit, metadata.languages)),
            keywords=metadata.keywords,
            spatial=self.visit(metadata.spatial),
            temporal=self.visit(metadata.temporal),
            sources=list(map(self.visit, metadata.sources)),
            license=self.visit(metadata.license),
            contributors=list(map(self.visit, metadata.contributors)),
            resources=list(map(self.visit, metadata.resources)),
            comment=self.visit(metadata.comment)
        )


