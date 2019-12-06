from typing import Dict
from typing import Tuple

from rdflib import BNode
from rdflib import Graph
from rdflib import Literal
from rdflib import URIRef
from rdflib.graph import Node
from rdflib.namespace import DCTERMS
from rdflib.namespace import FOAF
from rdflib.namespace import RDF
from rdflib.namespace import XSD

from omi import structure
from omi.dialects.base.compiler import Compiler
from omi.dialects.rdf.licenses import LICENSE_DICT
from omi.dialects.rdf.namespace import ADMS
from omi.dialects.rdf.namespace import DCAT
from omi.dialects.rdf.namespace import DCATDE
from omi.dialects.rdf.namespace import OEO
from omi.dialects.rdf.namespace import SCHEMA
from omi.dialects.rdf.namespace import SKOS
from omi.dialects.rdf.namespace import SPDX

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

    def visit_agency(self, agency: structure.Agency, *args, **kwargs):
        node = BNode()
        self._add_literal_or_None(node, DCTERMS.title, agency.name)
        self._add_literal_or_None(node, OEO.has_logo, agency.logo)
        return node

    def visit_context(self, context: structure.Context, *args, **kwargs):

        return (
            Literal(context.homepage),
            Literal(context.contact),
            Literal(context.documentation),
            Literal(context.source_code),
            Literal(context.grant_number),
            self.visit(context.funding_agency),
            self.visit(context.publisher),
        )

    def visit_person(self, person: structure.Person, *args, **kwargs):

        node = BNode()
        self.graph.add((node, RDF.type, FOAF.Person))
        self._add_literal_or_None(node, FOAF.name, person.name)
        self._add_literal_or_None(node, FOAF.mbox, person.email)
        return node

    def visit_contribution(self, contribution: structure.Contribution, *args, **kwargs):
        c = BNode()
        self.graph.add(
            (
                c,
                DCTERMS.contributor,
                self.visit(contribution.contributor, *args, **kwargs),
            )
        )
        self._add_literal_or_None(
            c, OEO.date, contribution.date.strftime("%Y-%m-%d"), datatype=XSD.date
        )
        self._add_literal_or_None(c, OEO.comment, contribution.comment)
        self._add_literal_or_None(c, OEO.object, contribution.object)
        return c

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return URIRef(LANG_DICT[language])

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        node = BNode()
        self._add_literal_or_None(node, SKOS.prefLabel, spatial.extent)
        self._add_literal_or_None(node, OEO.has_spatial_resolution, spatial.resolution)
        self._add_literal_or_None(node, OEO.location, spatial.location)
        return node

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        node = BNode()
        self.graph.add((node, RDF.type, DCTERMS.PeriodOfTime))
        self._add_literal_or_None(node, SCHEMA.startDate, temporal.ts_start)
        self._add_literal_or_None(node, SCHEMA.endDate, temporal.ts_end)
        self._add_literal_or_None(node, OEO.has_time_resolution, temporal.ts_resolution)
        self._add_literal_or_None(node, OEO.referenceDate, temporal.reference_date)
        self.graph.add(
            (node, OEO.has_timestamp_alignment, self.visit(temporal.ts_orientation))
        )
        self._add_literal_or_None(node, OEO.uses_aggregation, temporal.aggregation)
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
        self._add_literal_or_None(node, DCTERMS.title, source.title)
        self._add_literal_or_None(node, DCTERMS.description, source.description)
        self._add_literal_or_None(node, FOAF.page, source.path)
        for l in source.licenses:
            li = self.visit(l, **kwargs)
            self.graph.add((node, OEO.has_terms_of_use, li))
        return node

    def visit_terms_of_use(self, tou: structure.TermsOfUse, *args, **kwargs):
        node = BNode()
        self._add_literal_or_None(
            node, DCATDE.licenseAttributionByText, tou.attribution
        )
        self._add_literal_or_None(node, OEO.has_instruction, tou.instruction)
        self.graph.add((node, DCAT.license, self.visit(tou.license, **kwargs)))
        return node

    def visit_license(self, lic: structure.License, *args, license_dict=None, **kwargs):
        if False:  # lic.name in LICENSE_DICT:
            li = URIRef(LICENSE_DICT[lic.identifier])
        else:
            if license_dict is not None and lic.identifier in license_dict:
                li = license_dict[lic.identifier]
            else:
                li = BNode()
                self.graph.add((li, RDF.type, DCAT.LicenseDocument))
                if lic.other_references:
                    for ref in lic.other_references:
                        self._add_literal_or_None(li, SPDX.seeAlso, ref)
                self._add_literal_or_None(li, FOAF.page, lic.path)
                self._add_literal_or_None(li, SPDX.licenseId, lic.identifier)
                if lic.text:
                    self._add_literal_or_None(li, SPDX.licenseText, lic.text)
                self._add_literal_or_None(li, SPDX.name, lic.name)
                if license_dict is not None and lic.identifier is not None:
                    license_dict[lic.identifier] = li
        return li

    def visit_resource(
        self,
        resource: structure.Resource,
        *args,
        resource_dict: Dict[str, Tuple[Node, Dict[str, Node]]] = None,
        **kwargs
    ):
        s = BNode()
        self.graph.add((s, RDF.type, DCAT.Distribution))
        self._add_literal_or_None(s, DCTERMS.title, resource.name)
        self._add_literal_or_None(s, DCAT.accessURL, resource.path)
        self._add_literal_or_None(s, OEO.has_format, resource.format)  # dct:format ?
        self._add_literal_or_None(s, OEO.profile, resource.profile)
        self._add_literal_or_None(s, OEO.encoding, resource.encoding)
        if resource.dialect is not None:
            self.graph.add((s, OEO.has_dialect, self.visit(resource.dialect)))
        fields, pks, fks = self.visit(resource.schema, s, resource_dict=resource_dict)
        for f in fields:
            self.graph.add((s, OEO.field, f))
        for pk in pks:
            self.graph.add((s, OEO.primaryKey, pk))
        for fk in fks:
            self.graph.add((s, OEO.has_foreignKey, fk))
        return s

    def visit_schema(
        self,
        schema: structure.Schema,
        *args,
        resource_dict: Dict[str, Tuple[Node, Dict[str, Node]]] = None,
        **kwargs
    ):
        resource_node = args[0]
        field_dict = dict()
        fields = []
        resource_dict = resource_dict or dict()
        for field in schema.fields:
            fnode = self.visit(field, *args, **kwargs)
            fields.append(fnode)
            field_dict[field.name] = fnode

        pks = [field_dict[pk] for pk in schema.primary_key or []]

        resource_name = schema.fields[0].resource.name

        if resource_name in resource_dict:
            resource_dict[resource_name][1].update(field_dict)
        else:
            resource_dict[resource_name] = (resource_node, field_dict)

        fks = [
            self.visit(fk, *args, resource_dict=resource_dict, **kwargs)
            for fk in schema.foreign_keys or []
        ]

        return fields, pks, fks

    def visit_dialect(self, dialect: structure.Dialect, *args, **kwargs):
        node = BNode()
        self._add_literal_or_None(node, OEO.delimiter, dialect.delimiter)
        self._add_literal_or_None(node, OEO.decimalSeparator, dialect.decimal_separator)
        return node

    def visit_field(self, field: structure.Field, *args, **kwargs):
        field_uri = BNode()
        self.graph.add((field_uri, RDF.type, OEO.DatabaseField))
        self._add_literal_or_None(field_uri, DCTERMS.title, field.name)
        self._add_literal_or_None(field_uri, DCTERMS.description, field.description)
        self._add_literal_or_None(field_uri, OEO.type, field.type)
        self._add_literal_or_None(field_uri, OEO.unit, field.unit)
        return field_uri

    def visit_foreign_key(
        self, foreign_key: structure.ForeignKey, *args, resource_dict=None, **kwargs
    ):
        fk_node = BNode()
        for r in foreign_key.references:
            self.graph.add(
                (
                    fk_node,
                    OEO.has_reference,
                    self.visit(r, *args, resource_dict=resource_dict, **kwargs),
                )
            )
        return fk_node

    def visit_reference(
        self,
        reference: structure.Reference,
        *args,
        resource_dict: Dict[str, Tuple[Node, Dict[str, Node]]] = None,
        **kwargs
    ):
        r_node = BNode()
        self.graph.add(
            (r_node, OEO.has_source, self._get_field(reference.source, resource_dict))
        )
        target = self._get_or_create_field(
            reference.target, resource_dict, *args, **kwargs
        )
        self.graph.add((r_node, OEO.has_target, target))
        return r_node

    def visit_review(self, review: structure.Review, *args, **kwargs):
        node = BNode()
        self.graph.add((node, FOAF.page, URIRef(review.path)))
        self._add_literal_or_None(node, OEO.has_badge, review.badge)
        return node

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        com = BNode()
        self._add_literal_or_None(com, OEO.metadata_info, comment.metadata_info)
        self._add_literal_or_None(com, OEO.dates_info, comment.dates)
        self._add_literal_or_None(com, OEO.units_info, comment.units)
        self._add_literal_or_None(com, OEO.languages_info, comment.languages)
        self._add_literal_or_None(com, OEO.licenses_info, comment.licenses)
        self._add_literal_or_None(com, OEO.review_info, comment.review)
        self._add_literal_or_None(com, OEO.none_info, comment.none)
        return com

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        datasetURI = URIRef(metadata.identifier)

        license_dict = kwargs.get("license_dict", {})

        self.graph.add((datasetURI, RDF.type, DCAT.Dataset))
        self._add_literal_or_None(datasetURI, ADMS.Identifier, metadata.name)
        self._add_literal_or_None(datasetURI, DCTERMS.title, metadata.title)
        self._add_literal_or_None(datasetURI, DCTERMS.description, metadata.description)

        for lang in metadata.languages:
            self._add_literal_or_None(datasetURI, DCTERMS.language, self.visit(lang))

        for k in metadata.keywords:
            self._add_literal_or_None(datasetURI, DCAT.keyword, k)

        self.graph.add(
            (
                datasetURI,
                OEO.publicationDate,
                Literal(
                    metadata.publication_date.strftime("%Y-%m-%d"), datatype=XSD.date
                ),
            )
        )

        homepage, contact, documentation, source_code, grant_number, funding_agency, publisher = self.visit(
            metadata.context
        )

        self.graph.add((datasetURI, FOAF.homepage, homepage))
        self.graph.add((datasetURI, DCAT.contactpoint, contact))
        self.graph.add((datasetURI, OEO.documentation, documentation))
        self.graph.add((datasetURI, OEO.sourceCode, source_code))
        self.graph.add((datasetURI, OEO.grantNo, grant_number))

        if funding_agency:
            self.graph.add((datasetURI, OEO.has_funding_agency, funding_agency))

        if publisher:
            self.graph.add((datasetURI, OEO.has_publisher, publisher))

        self.graph.add((datasetURI, DCTERMS.spatial, self.visit(metadata.spatial)))
        self.graph.add((datasetURI, DCTERMS.temporal, self.visit(metadata.temporal)))
        for s in metadata.sources:
            self.graph.add(
                (datasetURI, DCTERMS.source, self.visit(s, license_dict=license_dict))
            )
        for l in metadata.license:
            self.graph.add(
                (
                    datasetURI,
                    OEO.has_terms_of_use,
                    self.visit(l, license_dict=license_dict),
                )
            )

        for c in metadata.contributions:
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

        return datasetURI

    def _get_or_create_field(
        self,
        field: structure.Field,
        resource_dict: Dict[str, Tuple[Node, Dict[str, Node]]],
        *args,
        **kwargs
    ):
        try:
            if field.resource.name not in resource_dict:
                self.visit_resource(field.resource, resource_dict=resource_dict)
            return self._get_field(field, resource_dict)
        except FieldNotFoundError:
            f = self.visit_field(field, *args, **kwargs)
            res_node, field_dict = resource_dict[field.resource.name]
            self.graph.add((res_node, OEO.field, f))
            field_dict[field.name] = f
            return f

    def _get_field(
        self,
        field: structure.Field,
        resource_dict: Dict[str, Tuple[Node, Dict[str, Node]]],
    ):
        res = resource_dict.get(field.resource.name)
        if res is None:
            raise ResourceNotFoundError(field.resource.name)
        node = res[1].get(field.name)
        if node is None:
            raise FieldNotFoundError(field.name)
        return node

    def _add_literal_or_None(self, subject: Node, predicate, obj: str, **kwargs):
        if obj is not None:
            self.graph.add((subject, predicate, Literal(obj, **kwargs)))


class FieldNotFoundError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass
