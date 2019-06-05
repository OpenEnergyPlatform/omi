from rdflib import BNode
from rdflib import Graph
from rdflib import Literal
from rdflib import URIRef
from rdflib.graph import Node
from rdflib.namespace import DCTERMS
from rdflib.namespace import FOAF
from rdflib.namespace import RDF
from rdflib.namespace import XSD

from metadata_tool import structure
from metadata_tool.dialects.base.compiler import Compiler
from metadata_tool.dialects.rdf.licenses import LICENSE_DICT
from metadata_tool.dialects.rdf.namespace import ADMS
from metadata_tool.dialects.rdf.namespace import DCAT
from metadata_tool.dialects.rdf.namespace import DCATDE
from metadata_tool.dialects.rdf.namespace import OEO
from metadata_tool.dialects.rdf.namespace import SCHEMA
from metadata_tool.dialects.rdf.namespace import SKOS

from typing import Dict, Iterable

LANG_DICT = {
    "eng": "http://publications.europa.eu/resource/authority/language/ENG",
    "en-GB": "http://publications.europa.eu/resource/authority/language/ENG",
    "ger": "http://publications.europa.eu/resource/authority/language/GER",
    "en-US": "",
    "de-DE": "http://publications.europa.eu/resource/authority/language/GER",
    "fr-FR": "",
}


class RDFCompiler(Compiler):
    def visit_context(self, context: structure.Context, *args, **kwargs):
        return (
            Literal(context.homepage),
            Literal(context.contact),
            Literal(context.documentation),
            Literal(context.source_code),
            Literal(context.grant_number),
        )

    def visit_person(self, person: structure.Person, *args, **kwargs):
        graph = args[0]
        node = BNode()
        graph.add((node, RDF.type, FOAF.Person))
        graph.add((node, FOAF.name, Literal(person.name)))
        graph.add((node, FOAF.mbox, Literal(person.email)))
        return node

    def visit_contributor(self, contributor: structure.Contributor, *args, **kwargs):
        graph = args[0]
        c = BNode()
        graph.add(
            (
                c,
                DCTERMS.contributor,
                self.visit(contributor.contributor, *args, **kwargs),
            )
        )
        graph.add((c, OEO.date, Literal(contributor.date, datatype=XSD.date)))
        graph.add((c, OEO.comment, Literal(contributor.comment)))
        graph.add((c, OEO.object, Literal(contributor.object)))
        return c

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return URIRef(LANG_DICT[language])

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        graph = args[0]
        node = BNode()
        graph.add((node, SKOS.prefLabel, Literal(spatial.extent)))
        graph.add((node, OEO.has_spatial_resolution, Literal(spatial.resolution)))
        graph.add((node, OEO.location, Literal(spatial.location)))
        return node

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        graph = args[0]
        node = BNode()
        graph.add((node, RDF.type, DCTERMS.PeriodOfTime))
        graph.add((node, SCHEMA.startDate, Literal(temporal.ts_start)))
        graph.add((node, SCHEMA.endDate, Literal(temporal.ts_end)))
        graph.add((node, OEO.has_time_resolution, Literal(temporal.ts_resolution)))
        graph.add((node, OEO.referenceDate, Literal(temporal.reference_date)))
        graph.add(
            (node, OEO.has_orientation, self.visit(temporal.ts_orientation, graph))
        )
        return node

    def visit_timestamp_orientation(
        self, ts_orientation: structure.TimestampOrientation, *args, **kwargs
    ):
        if ts_orientation == structure.TimestampOrientation.left:
            return OEO.left_orientation
        elif ts_orientation == structure.TimestampOrientation.middle:
            return OEO.middle_orientation
        elif ts_orientation == structure.TimestampOrientation.right:
            return OEO.right_orientation
        else:
            raise Exception("Unknown timestamp orientation")

    def visit_source(self, source: structure.Source, *args, **kwargs):
        graph = args[0]
        node = BNode()
        graph.add((node, DCTERMS.title, Literal(source.title)))
        graph.add((node, DCTERMS.description, Literal(source.description)))
        graph.add((node, FOAF.page, Literal(source.path)))
        if source.license.title in LICENSE_DICT:
            li = URIRef(LICENSE_DICT[source.license.title])
        else:
            li = Literal(source.license.title)
        graph.add((node, DCTERMS.license, li))
        graph.add((node, DCTERMS.rights, Literal(source.copyright)))
        return node

    def visit_license(self, lic: structure.License, *args, **kwargs):
        graph = args[0]
        if lic.name in LICENSE_DICT:
            li = URIRef(LICENSE_DICT[lic.name])
        else:
            li = BNode()
            graph.add((li, RDF.type, DCTERMS.LicenseDocument))
            graph.add((li, DCTERMS.title, Literal(lic.name)))
            graph.add((li, DCTERMS.title, Literal(lic.title)))
            graph.add((li, OEO.path, Literal(lic.path)))
        return Literal(lic.attribution), Literal(lic.instruction), li

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        graph = args[0]
        s = BNode()
        graph.add((s, RDF.type, DCAT.Distribution))
        graph.add((s, DCTERMS.title, Literal(resource.name)))
        graph.add((s, DCAT.accessURL, Literal(resource.path)))
        graph.add((s, OEO.has_format, Literal(resource.format)))  # dct:format ?
        graph.add((s, OEO.profile, Literal(resource.profile)))
        graph.add((s, OEO.encoding, Literal(resource.encoding)))
        graph.add((s, OEO.has_dialect, self.visit(resource.dialect, graph)))
        fields, pks, fks = self.visit(resource.schema, graph)
        for f in fields:
            graph.add((s, OEO.field, f))
        for pk in pks:
            graph.add((s, OEO.primaryKey, pk))
        for fk in fks:
            graph.add((s, OEO.has_foreignKey, fk))
        return s

    def visit_schema(self, schema: structure.Schema, *args, **kwargs):
        field_dict = dict()
        fields = []
        for field in schema.fields:
            fnode = self.visit(field, *args, **kwargs)
            fields.append(fnode)
            field_dict[field.name] = fnode

        pks = [field_dict[pk] for pk in schema.primary_key]

        if schema.fields:
            resource_dict = {schema.fields[0].resource.name: field_dict}
        else:
            resource_dict = {}

        fks = [
            self.visit(fk, *args, resouce_dict=resource_dict, **kwargs)
            for fk in schema.foreign_keys
        ]

        return fields, pks, fks

    def visit_dialect(self, dialect: structure.Dialect, *args, **kwargs):
        graph = args[0]
        node = BNode()
        graph.add((node, OEO.delimiter, Literal(dialect.delimiter)))
        graph.add((node, OEO.decimalSeparator, Literal(dialect.decimal_separator)))
        return node

    def visit_field(self, field: structure.Field, *args, **kwargs):
        graph = args[0]
        field_uri = BNode()
        graph.add((field_uri, RDF.type, OEO.DatabaseField))
        graph.add((field_uri, DCTERMS.title, Literal(field.name)))
        graph.add((field_uri, DCTERMS.description, Literal(field.description)))
        graph.add((field_uri, OEO.type, Literal(field.type)))
        graph.add((field_uri, OEO.unit, Literal(field.unit)))
        return field_uri

    def visit_foreign_key(
        self, foreign_key: structure.ForeignKey, *args, resouce_dict=None, **kwargs
    ):
        graph = args[0]
        fk_node = BNode()
        for r in foreign_key.references:
            graph.add(
                (
                    fk_node,
                    OEO.has_reference,
                    self.visit(r, graph, *args, resouce_dict=resouce_dict, **kwargs),
                )
            )
        return fk_node

    def visit_reference(
        self, reference: structure.Reference, *args, resouce_dict=None, **kwargs
    ):
        graph = args[0]
        r_node = BNode()
        graph.add(
            (r_node, OEO.has_source, self._get_field(reference.source, resouce_dict))
        )
        graph.add(
            (
                r_node,
                OEO.has_target,
                self._get_or_create_field(
                    reference.target, resouce_dict, *args, **kwargs
                ),
            )
        )
        return r_node

    def visit_review(self, review: structure.Review, *args, **kwargs):
        graph = args[0]
        node = BNode()
        graph.add((node, OEO.path, URIRef(review.path)))
        graph.add((node, OEO.has_badge, Literal(review.badge)))
        return node

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        graph = args[0]
        com = BNode()
        graph.add((com, OEO.metadata_info, Literal(comment.metadata_info)))
        graph.add((com, OEO.dates_info, Literal(comment.dates)))
        graph.add((com, OEO.units_info, Literal(comment.units)))
        graph.add((com, OEO.languages_info, Literal(comment.languages)))
        graph.add((com, OEO.licenses_info, Literal(comment.licenses)))
        graph.add((com, OEO.review_info, Literal(comment.review)))
        graph.add((com, OEO.none_info, Literal(comment.none)))
        return com

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        g = Graph()
        g.namespace_manager.bind("foaf", FOAF)
        g.namespace_manager.bind("dct", DCTERMS)
        g.namespace_manager.bind("dcat", DCAT)
        g.namespace_manager.bind("dcatde", DCATDE)
        g.namespace_manager.bind("oeo", OEO)
        g.namespace_manager.bind("schema", SCHEMA)
        g.namespace_manager.bind("skos", SKOS)
        g.namespace_manager.bind("adms", ADMS)

        datasetURI = URIRef(metadata.identifier)

        g.add((datasetURI, RDF.type, DCAT.Dataset))
        g.add((datasetURI, ADMS.Identifier, Literal(metadata.title)))
        g.add((datasetURI, DCTERMS.title, Literal(metadata.name)))
        g.add((datasetURI, DCTERMS.description, Literal(metadata.description)))

        for lang in metadata.languages:
            g.add((datasetURI, DCTERMS.language, Literal(self.visit(lang))))

        for k in metadata.keywords:
            g.add((datasetURI, DCAT.keyword, Literal(k)))

        g.add(
            (
                datasetURI,
                OEO.publicationDate,
                Literal(metadata.publication_date, datatype=XSD.date),
            )
        )

        homepage, contact, documentation, source_code, grant_number = self.visit(
            metadata.context, g
        )

        g.add((datasetURI, FOAF.homepage, homepage))
        g.add((datasetURI, DCAT.contactpoint, contact))
        g.add((datasetURI, OEO.documentation, documentation))
        g.add((datasetURI, OEO.sourceCode, source_code))
        g.add((datasetURI, OEO.grantNo, grant_number))

        g.add((datasetURI, DCTERMS.spatial, self.visit(metadata.spatial, g)))
        g.add((datasetURI, DCTERMS.temporal, self.visit(metadata.temporal, g)))
        for s in metadata.sources:
            g.add((datasetURI, DCTERMS.source, self.visit(s, g)))
        for l in metadata.license:
            attribution, instruction, license_node = self.visit(l, g)
            g.add((datasetURI, DCATDE.licenseAttributionByText, attribution))
            g.add((datasetURI, DCATDE.licenseAttributionByText, instruction))
            g.add((datasetURI, DCTERMS.license, license_node))
        for c in metadata.contributors:
            g.add((datasetURI, DCTERMS.contributor, self.visit(c, g)))
        for r in metadata.resources:
            g.add((datasetURI, OEO.has_resource, self.visit(r, g)))

        g.add((datasetURI, OEO.review, self.visit(metadata.review, g)))

        g.add(
            (
                datasetURI,
                OEO.metadataLicense,
                URIRef("https://creativecommons.org/publicdomain/zero/1.0/legalcode"),
            )
        )

        g.add((datasetURI, OEO.comment, self.visit(metadata.comment, g)))

        return g.serialize(format="turtle").decode("utf-8")

    def _get_or_create_field(
        self,
        field: structure.Field,
        resource_dict: Dict[str, Dict[str, Node]],
        *args,
        **kwargs
    ):
        try:
            if field.resource.name not in resource_dict:
                resource_dict[field.resource.name] = {}
            return self._get_field(field, resource_dict)
        except FieldNotFoundError:
            f = self.visit_field(field, *args, **kwargs)
            resource_dict[field.resource.name][field.name] = f
            return f

    def _get_field(
        self, field: structure.Field, resource_dict: Dict[str, Dict[str, Node]]
    ):
        res = resource_dict.get(field.resource.name)
        if res is None:
            raise ResourceNotFoundError(field.resource.name)
        node = resource_dict[field.resource.name].get(field.name)
        if node is None:
            raise FieldNotFoundError(field.name)
        return node


class FieldNotFoundError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass
