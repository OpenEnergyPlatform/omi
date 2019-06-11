from typing import Dict

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
from metadata_tool.dialects.rdf.namespace import SPDX

LANG_DICT = {
    "eng": "http://publications.europa.eu/resource/authority/language/ENG",
    "en-GB": "http://publications.europa.eu/resource/authority/language/ENG",
    "ger": "http://publications.europa.eu/resource/authority/language/GER",
    "en-US": "",
    "de-DE": "http://publications.europa.eu/resource/authority/language/GER",
    "fr-FR": "",
}


class RDFCompiler(Compiler):

    def __init__(self, graph: Graph = None):
        if graph is None:
            self.graph = Graph()
            self.graph.namespace_manager.bind("foaf", FOAF)
            self.graph.namespace_manager.bind("dct", DCTERMS)
            self.graph.namespace_manager.bind("dcat", DCAT)
            self.graph.namespace_manager.bind("dcatde", DCATDE)
            self.graph.namespace_manager.bind("oeo", OEO)
            self.graph.namespace_manager.bind("schema", SCHEMA)
            self.graph.namespace_manager.bind("skos", SKOS)
            self.graph.namespace_manager.bind("adms", ADMS)
            self.graph.namespace_manager.bind("spdx", SPDX)
        else:
            self.graph = graph
    def visit_context(self, context: structure.Context, *args, **kwargs):
        return (
            Literal(context.homepage),
            Literal(context.contact),
            Literal(context.documentation),
            Literal(context.source_code),
            Literal(context.grant_number),
        )

    def visit_person(self, person: structure.Person, *args, **kwargs):

        node = BNode()
        self.graph.add((node, RDF.type, FOAF.Person))
        self.graph.add((node, FOAF.name, Literal(person.name)))
        self.graph.add((node, FOAF.mbox, Literal(person.email)))
        return node

    def visit_contributor(self, contributor: structure.Contributor, *args, **kwargs):
        c = BNode()
        self.graph.add(
            (
                c,
                DCTERMS.contributor,
                self.visit(contributor.contributor, *args, **kwargs),
            )
        )
        self.graph.add((c, OEO.date, Literal(contributor.date, datatype=XSD.date)))
        self.graph.add((c, OEO.comment, Literal(contributor.comment)))
        self.graph.add((c, OEO.object, Literal(contributor.object)))
        return c

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return URIRef(LANG_DICT[language])

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        node = BNode()
        self.graph.add((node, SKOS.prefLabel, Literal(spatial.extent)))
        self.graph.add((node, OEO.has_spatial_resolution, Literal(spatial.resolution)))
        self.graph.add((node, OEO.location, Literal(spatial.location)))
        return node

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        node = BNode()
        self.graph.add((node, RDF.type, DCTERMS.PeriodOfTime))
        self.graph.add((node, SCHEMA.startDate, Literal(temporal.ts_start)))
        self.graph.add((node, SCHEMA.endDate, Literal(temporal.ts_end)))
        self.graph.add((node, OEO.has_time_resolution, Literal(temporal.ts_resolution)))
        self.graph.add((node, OEO.referenceDate, Literal(temporal.reference_date)))
        self.graph.add(
            (node, OEO.has_orientation, self.visit(temporal.ts_orientation))
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
        node = BNode()
        self.graph.add((node, DCTERMS.title, Literal(source.title)))
        self.graph.add((node, DCTERMS.description, Literal(source.description)))
        self.graph.add((node, FOAF.page, Literal(source.path)))
        li = self.visit(source.license)
        self.graph.add((node, DCTERMS.license, li))
        self.graph.add((node, DCTERMS.rights, Literal(source.copyright)))
        return node

    def visit_terms_of_use(self, tou: structure.TermsOfUse, *args, **kwargs):
        node = BNode()
        self.graph.add((node, DCATDE.licenseAttributionByText, Literal(tou.attribution)))
        self.graph.add((node, OEO.has_instruction, Literal(tou.instruction)))
        self.graph.add((node, DCAT.license, self.visit(tou.license)))
        return node

    def visit_license(self, lic: structure.License, *args, **kwargs):
        if False:#lic.name in LICENSE_DICT:
            li = URIRef(LICENSE_DICT[lic.identifier])
        else:
            li = BNode()
            self.graph.add((li, RDF.type, DCAT.LicenseDocument))
            for ref in lic.other_references:
                self.graph.add((li, SPDX.seeAlso, Literal(ref)))
            self.graph.add((li, FOAF.page, Literal(lic.path)))
            self.graph.add((li, SPDX.licenseId, Literal(lic.identifier)))
            if lic.text:
                self.graph.add((li, SPDX.licenseText, Literal(lic.text)))
            self.graph.add((li, SPDX.name, Literal(lic.name)))
        return li

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        s = BNode()
        self.graph.add((s, RDF.type, DCAT.Distribution))
        self.graph.add((s, DCTERMS.title, Literal(resource.name)))
        self.graph.add((s, DCAT.accessURL, Literal(resource.path)))
        self.graph.add((s, OEO.has_format, Literal(resource.format)))  # dct:format ?
        self.graph.add((s, OEO.profile, Literal(resource.profile)))
        self.graph.add((s, OEO.encoding, Literal(resource.encoding)))
        self.graph.add((s, OEO.has_dialect, self.visit(resource.dialect)))
        fields, pks, fks = self.visit(resource.schema)
        for f in fields:
            self.graph.add((s, OEO.field, f))
        for pk in pks:
            self.graph.add((s, OEO.primaryKey, pk))
        for fk in fks:
            self.graph.add((s, OEO.has_foreignKey, fk))
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
        node = BNode()
        self.graph.add((node, OEO.delimiter, Literal(dialect.delimiter)))
        self.graph.add((node, OEO.decimalSeparator, Literal(dialect.decimal_separator)))
        return node

    def visit_field(self, field: structure.Field, *args, **kwargs):
        field_uri = BNode()
        self.graph.add((field_uri, RDF.type, OEO.DatabaseField))
        self.graph.add((field_uri, DCTERMS.title, Literal(field.name)))
        self.graph.add((field_uri, DCTERMS.description, Literal(field.description)))
        self.graph.add((field_uri, OEO.type, Literal(field.type)))
        self.graph.add((field_uri, OEO.unit, Literal(field.unit)))
        return field_uri

    def visit_foreign_key(
        self, foreign_key: structure.ForeignKey, *args, resouce_dict=None, **kwargs
    ):
        fk_node = BNode()
        for r in foreign_key.references:
            self.graph.add(
                (
                    fk_node,
                    OEO.has_reference,
                    self.visit(r, *args, resouce_dict=resouce_dict, **kwargs),
                )
            )
        return fk_node

    def visit_reference(
        self, reference: structure.Reference, *args, resouce_dict=None, **kwargs
    ):
        r_node = BNode()
        self.graph.add(
            (r_node, OEO.has_source, self._get_field(reference.source, resouce_dict))
        )
        self.graph.add(
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
        node = BNode()
        self.graph.add((node, FOAF.page, URIRef(review.path)))
        self.graph.add((node, OEO.has_badge, Literal(review.badge)))
        return node

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        com = BNode()
        self.graph.add((com, OEO.metadata_info, Literal(comment.metadata_info)))
        self.graph.add((com, OEO.dates_info, Literal(comment.dates)))
        self.graph.add((com, OEO.units_info, Literal(comment.units)))
        self.graph.add((com, OEO.languages_info, Literal(comment.languages)))
        self.graph.add((com, OEO.licenses_info, Literal(comment.licenses)))
        self.graph.add((com, OEO.review_info, Literal(comment.review)))
        self.graph.add((com, OEO.none_info, Literal(comment.none)))
        return com

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        datasetURI = URIRef(metadata.identifier)

        self.graph.add((datasetURI, RDF.type, DCAT.Dataset))
        self.graph.add((datasetURI, ADMS.Identifier, Literal(metadata.name)))
        self.graph.add((datasetURI, DCTERMS.title, Literal(metadata.title)))
        self.graph.add((datasetURI, DCTERMS.description, Literal(metadata.description)))

        for lang in metadata.languages:
            self.graph.add((datasetURI, DCTERMS.language, Literal(self.visit(lang))))

        for k in metadata.keywords:
            self.graph.add((datasetURI, DCAT.keyword, Literal(k)))

        self.graph.add(
            (
                datasetURI,
                OEO.publicationDate,
                Literal(metadata.publication_date, datatype=XSD.date),
            )
        )

        homepage, contact, documentation, source_code, grant_number = self.visit(
            metadata.context
        )

        self.graph.add((datasetURI, FOAF.homepage, homepage))
        self.graph.add((datasetURI, DCAT.contactpoint, contact))
        self.graph.add((datasetURI, OEO.documentation, documentation))
        self.graph.add((datasetURI, OEO.sourceCode, source_code))
        self.graph.add((datasetURI, OEO.grantNo, grant_number))

        self.graph.add((datasetURI, DCTERMS.spatial, self.visit(metadata.spatial)))
        self.graph.add((datasetURI, DCTERMS.temporal, self.visit(metadata.temporal)))
        for s in metadata.sources:
            self.graph.add((datasetURI, DCTERMS.source, self.visit(s)))
        for l in metadata.license:
            self.graph.add((datasetURI, OEO.has_terms_of_use, self.visit(l)))

        for c in metadata.contributors:
            self.graph.add((datasetURI, OEO.has_contribution, self.visit(c)))
        for r in metadata.resources:
            self.graph.add((datasetURI, OEO.has_resource, self.visit(r)))

        self.graph.add((datasetURI, OEO.has_review, self.visit(metadata.review)))

        self.graph.add(
            (
                datasetURI,
                OEO.metadataLicense,
                URIRef("https://creativecommons.org/publicdomain/zero/1.0/legalcode"),
            )
        )

        self.graph.add((datasetURI, OEO.comment, self.visit(metadata.comment)))

        return self.graph.serialize(format="turtle").decode("utf-8")

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

    def _add_literal_or_None(self,
                             subject: Node,
                             predicate,
                             obj: str):
        if obj is not None:
            self.graph.add((subject, predicate, Literal(obj)))

class FieldNotFoundError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass
