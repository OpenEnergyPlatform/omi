from metadata_tool import structure
from metadata_tool.dialects.base.compiler import Compiler
from metadata_tool.dialects.rdf.licenses import LICENSE_DICT
from rdflib import BNode
from rdflib import Graph
from rdflib import Literal
from rdflib import Namespace
from rdflib import URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS
from rdflib.namespace import FOAF
from rdflib.namespace import RDF
from rdflib.namespace import XSD
from rdflib.namespace import NamespaceManager

DCAT = Namespace("http://www.w3.org/ns/dcat#")
OEO = Namespace("http://openenergy-platform.org/ontology/v0.0.1/oeo/")
DCATDE = Namespace("http://dcat-ap.de/def/dcatde/")
SCHEMA = Namespace("http://schema.org/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ADMS = Namespace("http://www.w3.org/ns/adms#")


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
        # context
        graph = args[0]
        parent = args[2]
        graph.add(
            (parent, FOAF.homepage, Literal(context.homepage)))
        graph.add((parent, DCAT.contactpoint, Literal(context.contact)))
        graph.add((parent, OEO.documentation, Literal(context.documentation)))
        graph.add((parent, OEO.sourceCode, Literal(context.source_code)))
        graph.add((parent, OEO.grantNo, Literal(context.grant_number)))

    def visit_contributor(self, contributor: structure.Contributor, *args, **kwargs):
        graph = args[0]
        parent = args[1]
        c = BNode()
        graph.add((parent, DCTERMS.contributor, c))
        graph.add((c, RDF.type, FOAF.Person))
        graph.add((c, FOAF.name, Literal(contributor.title)))
        graph.add((c, FOAF.mbox, Literal(contributor.email)))
        graph.add((c, OEO.date, Literal(contributor.date, datatype=XSD.date)))
        graph.add(
            (c, OEO.comment, Literal(contributor.comment)))
        graph.add((c, OEO.object, Literal(contributor.object)))

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return URIRef(LANG_DICT[language])

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        graph = args[0]
        root = args[1]
        node = BNode()
        graph.add((root, DCTERMS.spatial, node))
        graph.add((node, SKOS.prefLabel, Literal(spatial.extent)))
        graph.add((
                node,
                OEO.has_spatial_resolution,
                Literal(spatial.resolution),
            )
        )
        graph.add((node, OEO.location, Literal(spatial.location)))
        return node

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        graph = args[0]
        parent = args[1]
        node = BNode()
        graph.add((parent, DCTERMS.temporal, node))
        graph.add((node, RDF.type, DCTERMS.PeriodOfTime))
        graph.add((node, SCHEMA.startDate, Literal(temporal.ts_start)))
        graph.add((node, SCHEMA.endDate, Literal(temporal.ts_end)))
        graph.add(
            (
                node,
                OEO.has_time_resolution,
                Literal(temporal.ts_resolution),
            )
        )
        graph.add(
            (
                node,
                OEO.referenceDate,
                Literal(temporal.reference_date),
            )
        )
        self.visit(temporal.ts_orientation, graph, node)
        return node

    def visit_timestamp_orientation(
        self, ts_orientation: structure.TimestampOrientation, *args, **kwargs
    ):
        graph = args[0]
        parent = args[1]

        if ts_orientation == structure.TimestampOrientation.left:
            v = "left"
        elif ts_orientation == structure.TimestampOrientation.middle:
            v = "middle"
        elif ts_orientation == structure.TimestampOrientation.right:
            v = "right"
        else:
            raise Exception("Unknown timestamp orientation")
        graph.add(
            (
                parent,
                OEO.has_orientation,
                Literal(v),
            )
        )

    def visit_source(self, source: structure.Source, *args, **kwargs):
        graph = args[0]
        parent = args[1]
        node = BNode()
        graph.add((parent, DCTERMS.source, node))
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
        parent = args[1]

        graph.add(
            (
                parent,
                DCATDE.licenseAttributionByText,
                Literal(lic.attribution),
            )
        )
        graph.add(
            (
                parent,
                DCATDE.licenseAttributionByText,
                Literal(lic.instruction),
            )
        )
        if lic.name in LICENSE_DICT:
            li = URIRef(LICENSE_DICT[lic.name])
        else:
            li = BNode()
            graph.add((li, RDF.type, DCTERMS.LicenseDocument))
            graph.add((parent, DCTERMS.title, Literal(lic.name)))
            graph.add((li, DCTERMS.title, Literal(lic.title)))
            graph.add((li, OEO.path, Literal(lic.path)))
        graph.add((parent, DCTERMS.license, li))
        return li

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        graph = args[0]
        parent = args[2]
        s = BNode()
        graph.add((s, RDF.type, DCAT.Distribution))
        graph.add((s, DCTERMS.title, Literal(resource.name)))
        graph.add((s, DCAT.accessURL, Literal(resource.path)))
        graph.add((s, OEO.has_format, Literal(resource.format)))  # dct:format ?
        graph.add((s, OEO.profile, Literal(resource.profile)))
        graph.add((s, OEO.encoding, Literal(resource.encoding)))
        graph.add((parent, OEO.has_resource, s))

    def visit_schema(self, schema: structure.Schema, *args, **kwargs):
        graph = args[0]
        field_dict = dict([self.visit(field, *args, **kwargs)] for field in schema.fields)

        for pk in schema.primary_key:
            graph.add((field_dict[pk], OEO.primaryKey, Literal(pk)))

        for fk in schema.foreign_keys:
            self.visit(fk, *args, **kwargs)

    def visit_dialect(self, dialect: structure.Dialect, *args, **kwargs):
        graph = args[0]
        parent = args[2]
        node = BNode()
        graph.add((parent, OEO.dialect, node))
        graph.add((node, OEO.delimiter, Literal(dialect.delimiter)))
        graph.add(
            (
                node,
                OEO.decimalSeparator,
                Literal(dialect.decimal_separator),
            )
        )

    def visit_field(self, field: structure.Field, *args, **kwargs):
        graph = args[0]
        parent = args[2]
        field_uri = BNode()
        graph.add((parent, OEO.fields, field_uri))
        graph.add((field_uri, DCTERMS.title, Literal(field.name)))
        graph.add((field_uri, DCTERMS.description,
                   Literal(field.description)))
        graph.add((field_uri, OEO.type, Literal(field.type)))
        graph.add((field_uri, OEO.unit, Literal(field.unit)))

        return (field.name, field_uri)

    def visit_foreign_key(self, foreign_key: structure.ForeignKey, *args, **kwargs):
        graph = args[0]
        parent = args[2]
        foreignKey = BNode()
        graph.add((parent, OEO.has_foreignKey, foreignKey))
        graph.add(
            (foreignKey, OEO.fields,
             Literal(fk.fields))
        )
        reference = BNode()

    def visit_reference(self, reference: structure.Reference, *args, **kwargs):
        graph = args[0]
        parent = args[2]
        node = BNode()
        graph.add((parent, OEO.reference, reference))
        graph.add(
            (
                reference,
                OEO.ressource,
                Literal(
                    fk["reference"]["ressource"]),
            )
        )
        graph.add(
            (
                reference,
                OEO.fields,
                Literal(d["schema"]["foreignKeys"]["reference"]["fields"]),
            )
        )

    def visit_review(self, review: structure.Review, *args, **kwargs):
        graph = args[0]
        parent = args[2]
        node = BNode()
        graph.add((parent, OEO.review, node))
        graph.add((node, OEO.path, URIRef(review.path)))
        graph.add((node, OEO.has_badge, Literal(review.badge)))

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        # metaMetadata
        return dict(
            metadata=Literal(comment.metadata_info),
            dates=Literal(comment.dates),
            units=Literal(comment.units),
            languages=Literal(comment.languages),
            licenses=Literal(comment.licenses),
            review=Literal(comment.review),
            none=Literal(comment.none))

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
        g.add((datasetURI, DCTERMS.title, Literal(metadata.title)))
        g.add((datasetURI, DCTERMS.title, Literal(metadata.name)))
        g.add((datasetURI, ADMS.Identifier, Literal(metadata.identifier)))
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

        self.visit(metadata.context, g, datasetURI, datasetURI)
        spatial = self.visit(metadata.spatial, g, datasetURI, datasetURI)
        temporal = self.visit(metadata.temporal, g, datasetURI, datasetURI)
        sources = [self.visit(s, g, datasetURI, datasetURI) for s in metadata.sources]
        licenses = [self.visit(l, g, datasetURI, datasetURI) for l in metadata.license]
        contributors = [self.visit(c, g, datasetURI, datasetURI) for c in metadata.contributors]
        resources = [self.visit(r, g, datasetURI, datasetURI) for r in metadata.resources]

        g.add((datasetURI, OEO.metadataLicense, URIRef("https://creativecommons.org/publicdomain/zero/1.0/legalcode")))

        comment_dict = self.visit(metadata.comment)

        return g.serialize(format="turtle").decode("utf-8")
