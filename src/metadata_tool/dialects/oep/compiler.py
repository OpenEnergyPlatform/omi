import json

from collections import OrderedDict

from metadata_tool import structure
from metadata_tool.dialects.base.compiler import Compiler


class JSONCompiler(Compiler):
    __METADATA_VERSION = "OEP-1.4"

    def visit_context(self, context: structure.Context):
        return OrderedDict(
            homepage=self.visit(context.homepage),
            documentation=self.visit(context.documentation),
            sourceCode=self.visit(context.source_code),
            contact=self.visit(context.contact),
            grantNo=self.visit(context.grant_number),
        )

    def visit_contributor(self, contributor: structure.Contributor):
        return OrderedDict(
            name=self.visit(contributor.name),
            email=self.visit(contributor.email),
            date=self.visit(contributor.date),
            comment=self.visit(contributor.comment),
        )

    def visit_language(self, language: structure.Language):
        return str(language)

    def visit_spatial(self, spatial: structure.Spatial):
        return OrderedDict(
            location=self.visit(spatial.location),
            extend=self.visit(spatial.extend),
            resolution=self.visit(spatial.resolution),
        )

    def visit_temporal(self, temporal: structure.Temporal):
        return OrderedDict(
            reference_date=self.visit(temporal.reference_date),
            ts_start=self.visit(temporal.ts_start),
            ts_end=self.visit(temporal.ts_end),
            ts_resolution=self.visit(temporal.ts_resolution),
        )

    def visit_source(self, source: structure.Source):
        return OrderedDict(
            title=self.visit(source.title),
            description=self.visit(source.description),
            path=self.visit(source.path),
            license=self.visit(source.license.name),
            copyright=self.visit(source.copyright),
        )

    def visit_license(self, lic: structure.License):
        return OrderedDict(
            name=self.visit(lic.name),
            title=self.visit(lic.title),
            path=self.visit(lic.path),
            instruction=self.visit(lic.instruction),
            attribution=self.visit(lic.attribution),
        )

    def visit_resource(self, resource: structure.Resource):
        return OrderedDict(
            profile=self.visit(resource.profile),
            name=self.visit(resource.name),
            path=self.visit(resource.path),
            format=self.visit(resource.name),
            encoding=self.visit(resource.encoding),
            schema=self.visit(resource.schema),
        )

    def visit_field(self, field: structure.Field):
        return OrderedDict(
            name=field.name,
            description=field.description,
            type=field.type,
            unit=field.unit,
        )

    def visit_schema(self, schema: structure.Schema):
        return OrderedDict(
            fields=list(map(self.visit, schema.fields)),
            primaryKey=self.visit(schema.primary_key),
            foreignKeys=list(map(self.visit, schema.foreign_keys)),
        )

    def visit_foreign_key(self, foreign_key: structure.ForeignKey):
        return OrderedDict(
            fields=self.visit(foreign_key.fields),
            reference=self.visit(foreign_key.reference),
        )

    def visit_reference(self, reference: structure.Reference):
        return OrderedDict(
            resource=self.visit(reference.resource), fields=self.visit(reference.fields)
        )

    def visit_review(self, review: structure.Review):
        return OrderedDict(path=review.path, badge=review.badge)

    def visit_meta_comment(self, comment: structure.MetaComment):
        return OrderedDict(
            metadata=comment.metadata_info,
            dates=comment.dates,
            units=comment.units,
            languages=comment.languages,
            licenses=comment.licenses,
            review=comment.review,
            none=comment.none,
        )

    def visit_metadata(self, metadata: structure.OEPMetadata):
        return OrderedDict(
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
            metaMetadata=OrderedDict(
                metadataVersion=self.__METADATA_VERSION,
                metadataLicense=OrderedDict(
                    name="CC0-1.0",
                    title="Creative Commons Zero v1.0 Universal",
                    path="https://creativecommons.org/publicdomain/zero/1.0/",
                ),
            ),
            comment=self.visit(metadata.comment),
        )


class MyJSONEncoder(json.JSONEncoder):
    """This enconder sets up a structured oder of the json string when transforming it from a python OrderedDict

    """

    def __init__(self, *args, **kwargs):
        super(MyJSONEncoder, self).__init__(*args, **kwargs)
        self.current_indent = 0
        self.current_indent_str = ""

    def encode(self, o):
        # Special Processing for lists
        if isinstance(o, (list, tuple)):
            primitives_only = True
            for item in o:
                if isinstance(item, (list, tuple, OrderedDict)):
                    primitives_only = False
                    break
            output = []
            if primitives_only:
                for item in o:
                    output.append(json.dumps(item))
                return "[ " + ", ".join(output) + "  ]"
            else:
                self.current_indent += 2
                self.current_indent_str = "".join(
                    [" " for x in range(self.current_indent)]
                )
                liste = []
                for item in o:
                    output = []
                    # This is performed if in the list is a OrderedDict
                    if isinstance(item, OrderedDict):
                        for key, value in item.items():
                            output.append(json.dumps(key) + ": " + self.encode(value))

                        liste.append(
                            "\n"
                            + 2 * self.current_indent_str
                            + "{"
                            + (",\n" + 2 * self.current_indent_str).join(output)
                            + "}"
                        )

                    else:
                        raise AssertionError(
                            "Only OrderedDicts in lists are properly structured. Please redefine it in the encode function."
                        )
                        output.append(self.current_indent_str + self.encode(item))
                        return "[\n" + ",".join(output) + "]"

                self.current_indent -= 2
                self.current_indent_str = "".join(
                    [" " for x in range(self.current_indent)]
                )

            return "[" + ",".join(liste) + "]"

        elif isinstance(o, OrderedDict):
            output = []
            self.current_indent += 4
            self.current_indent_str = "".join([" " for x in range(self.current_indent)])
            for key, value in o.items():
                output.append(
                    self.current_indent_str
                    + json.dumps(key)
                    + ": "
                    + self.encode(value)
                )
            self.current_indent -= 4
            self.current_indent_str = "".join([" " for x in range(self.current_indent)])
            return "{\n" + ",\n".join(output) + "}"
        else:
            return json.dumps(o)
