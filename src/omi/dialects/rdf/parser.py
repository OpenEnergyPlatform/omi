from typing import Dict
from typing import Iterable
from typing import Tuple

from dateutil.parser import parse as parse_date
from rdflib import Graph
from rdflib.graph import Node
from rdflib.graph import URIRef
from rdflib.namespace import DCTERMS
from rdflib.namespace import FOAF
from rdflib.namespace import RDF
from rdflib.namespace import RDFS

from omi import structure as struc
from omi.dialects.base.parser import Parser
from omi.dialects.rdf.namespace import ADMS
from omi.dialects.rdf.namespace import DCAT
from omi.dialects.rdf.namespace import DCATDE
from omi.dialects.rdf.namespace import OEO
from omi.dialects.rdf.namespace import SCHEMA
from omi.dialects.rdf.namespace import SKOS
from omi.dialects.rdf.namespace import SPDX


def _only(gen):
    r = _one_or_none(gen)
    if r is None:
        raise Exception("No matching elements")
    return r


def _one_str_or_none(gen):
    r = _one_or_none(gen)
    if r is None:
        return None
    return str(r)


def _one_or_none(gen):
    l = list(gen)
    if not l:
        return None
    if len(l) > 1:
        raise Exception("Found more than one match:" + str(l))
    return l[0]


class RDFParser(Parser):
    def load_string(self, string: str, *args, **kwargs):
        g = Graph()
        g.parse(data=string, format="ttl")
        return g

    def parse(self, graph, *args, **kwargs):
        for dataset in {s for s, _, _ in graph}.difference({o for _, _, o in graph}):
            if dataset in graph.subjects(RDF.type, DCAT.Dataset):
                return self.parse_metadata(graph, dataset)

    def parse_date(self, node: Node):
        return parse_date(node)

    def parse_context(self, graph: Graph, parent: Node) -> struc.Context:
        fa = _only(graph.objects(parent, OEO.has_funding_agency))
        kwargs = {}
        if fa is not None:
            kwargs["funding_agency"] = struc.Agency(
                name=_one_str_or_none(graph.objects(fa, DCTERMS.title)),
                logo=_one_str_or_none(graph.objects(fa, OEO.has_logo)),
            )
        pa = _only(graph.objects(parent, OEO.has_publisher))
        if pa is not None:
            kwargs["publisher"] = struc.Agency(
                name=_one_str_or_none(graph.objects(pa, DCTERMS.title)),
                logo=_one_str_or_none(graph.objects(pa, OEO.has_logo)),
            )
        return struc.Context(
            contact=_one_str_or_none(graph.objects(parent, DCAT.contactpoint)),
            documentation=_one_str_or_none(graph.objects(parent, OEO.documentation)),
            grant_number=_one_str_or_none(graph.objects(parent, OEO.grantNo)),
            homepage=_one_str_or_none(graph.objects(parent, FOAF.homepage)),
            source_code=_one_str_or_none(graph.objects(parent, OEO.sourceCode)),
            **kwargs
        )

    def parse_contributor(self, graph: Graph, parent: Node) -> struc.Contribution:
        return struc.Contribution(
            contributor=self.parse_person(
                graph, _only(graph.objects(parent, DCTERMS.contributor))
            ),
            date=self.parse_date(_only(graph.objects(parent, OEO.date))),
            obj=_one_str_or_none(graph.objects(parent, OEO.object)),
            comment=_one_str_or_none(graph.objects(parent, OEO.comment)),
        )

    def parse_person(self, graph, parent: Node):
        return struc.Person(
            name=_one_str_or_none(graph.objects(parent, FOAF.name)),
            email=_one_str_or_none(graph.objects(parent, FOAF.mbox)),
        )

    def parse_spatial(self, graph: Graph, parent: Node) -> struc.Spatial:
        return struc.Spatial(
            extent=_one_str_or_none(graph.objects(parent, SKOS.prefLabel)),
            location=_one_str_or_none(graph.objects(parent, OEO.location)),
            resolution=_one_str_or_none(
                graph.objects(parent, OEO.has_spatial_resolution)
            ),
        )

    def parse_temporal(self, graph: Graph, parent: Node) -> struc.Temporal:

        orientation = self.parse_timestamp_orientation(
            _only(graph.objects(parent, OEO.has_timestamp_alignment))
        )

        return struc.Temporal(
            start=self.parse_date(_only(graph.objects(parent, SCHEMA.startDate))),
            end=self.parse_date(_only(graph.objects(parent, SCHEMA.endDate))),
            ts_orientation=orientation,
            reference_date=self.parse_date(
                _only(graph.objects(parent, OEO.referenceDate))
            ),
            resolution=_one_str_or_none(graph.objects(parent, OEO.has_time_resolution)),
            aggregation=_one_str_or_none(graph.objects(parent, OEO.uses_aggregation)),
        )

    def parse_timestamp_orientation(self, node):
        if node == OEO.left_orientation:
            return struc.TimestampOrientation.left
        elif node == OEO.middle_orientation:
            return struc.TimestampOrientation.middle
        elif node == OEO.right_orientation:
            return struc.TimestampOrientation.right
        else:
            raise Exception("Unknown timestamp orientation: {}".format(node))

    def parse_source(self, graph: Graph, parent: Node) -> struc.Source:
        return struc.Source(
            title=_one_str_or_none(graph.objects(parent, DCTERMS.title)),
            description=_one_str_or_none(graph.objects(parent, DCTERMS.description)),
            path=_one_str_or_none(graph.objects(parent, FOAF.page)),
            licenses=[
                self.parse_terms_of_use(graph, tos)
                for tos in graph.objects(parent, OEO.has_terms_of_use)
            ],
        )

    def parse_terms_of_use(self, graph: Graph, parent: Node) -> struc.TermsOfUse:
        if isinstance(parent, URIRef):
            return None
        else:

            return struc.TermsOfUse(
                lic=self.parse_license(
                    graph, _only(graph.objects(parent, DCAT.license))
                ),
                attribution=str(
                    _only(graph.objects(parent, DCATDE.licenseAttributionByText))
                ),
                instruction=_one_str_or_none(
                    graph.objects(parent, OEO.has_instruction)
                ),
            )

    def parse_license(self, graph, parent: Node):
        kw = dict()
        for c in graph.objects(parent, RDFS.comment):
            kw["comment"] = _one_str_or_none(c)
        refs = list(graph.objects(parent, RDFS.seeAlso))
        return struc.License(
            name=_one_str_or_none(graph.objects(parent, SPDX.name)),
            identifier=_one_str_or_none(graph.objects(parent, SPDX.licenseId)),
            path=_one_str_or_none(graph.objects(parent, FOAF.page)),
            other_references=refs if refs else None,
            text=_one_str_or_none(graph.objects(parent, SPDX.licenseText)),
            **kw
        )

    def parse_resource(
        self,
        graph: Graph,
        parent: Node,
        resources: Dict[str, Tuple[struc.Resource, Dict[str, struc.Field]]] = None,
    ) -> struc.Resource:
        rname = _one_str_or_none(graph.objects(parent, DCTERMS.title))
        resources = resources or dict()
        if resources and rname in resources:
            return resources[rname][0]
        else:
            dialect_node = _one_or_none(graph.objects(parent, OEO.has_dialect))
            dialect = self.parse_dialect(graph, dialect_node) if dialect_node else None
            r = struc.Resource(
                dialect=dialect,
                encoding=_one_str_or_none(graph.objects(parent, OEO.encoding)),
                name=rname,
                path=_one_str_or_none(graph.objects(parent, DCAT.accessURL)),
                profile=_one_str_or_none(graph.objects(parent, OEO.profile)),
                resource_format=_one_str_or_none(graph.objects(parent, OEO.has_format)),
                schema=None,
            )
            r_fields = {}
            resources[rname] = r, r_fields
            schema = self.parse_schema(graph, parent, resources=resources)
            r.schema = schema
            for f in schema.fields:
                if f.name not in r_fields:
                    r_fields[f.name] = f
            return r

    def parse_schema(
        self,
        graph: Graph,
        parent: Node,
        resources: Dict[str, Tuple[Node, Iterable[Node]]] = None,
    ) -> struc.Schema:
        return struc.Schema(
            fields=[
                self.parse_field(graph, f) for f in graph.objects(parent, OEO.field)
            ],
            primary_key=[
                self.parse_field(graph, f).name
                for f in graph.objects(parent, OEO.primaryKey)
            ],
            foreign_keys=[
                self.parse_foreign_key(graph, f, resources=resources)
                for f in graph.objects(parent, OEO.has_foreignKey)
            ],
        )

    def parse_dialect(self, graph: Graph, parent: Node) -> struc.Dialect:
        delim = _one_or_none(graph.objects(parent, DCTERMS.delimiter))
        if delim is not None:
            delim = str(delim)
        return struc.Dialect(
            decimal_separator=_one_str_or_none(
                graph.objects(parent, OEO.decimalSeparator)
            ),
            delimiter=delim,
        )

    def parse_field(self, graph: Graph, parent: Node) -> struc.Field:
        return struc.Field(
            name=_one_str_or_none(graph.objects(parent, DCTERMS.title)),
            unit=_one_str_or_none(graph.objects(parent, OEO.unit)),
            field_type=_one_str_or_none(graph.objects(parent, OEO.type)),
            description=_one_str_or_none(graph.objects(parent, DCTERMS.description)),
        )

    def parse_foreign_key(
        self,
        graph: Graph,
        parent: Node,
        resources: Dict[str, Tuple[Node, Iterable[Node]]] = None,
    ) -> struc.ForeignKey:
        return struc.ForeignKey(
            references=[
                self.parse_reference(graph, r)
                for r in graph.objects(parent, OEO.has_reference)
            ]
        )

    def parse_reference(
        self,
        graph: Graph,
        parent: Node,
        resources: Dict[str, Tuple[Node, Iterable[Node]]] = None,
    ) -> struc.Reference:
        target_node = _only(graph.objects(parent, OEO.has_target))
        target_field = self.parse_field(graph, target_node)
        target_resource = self.parse_resource(
            graph, _only(graph.subjects(OEO.field, target_node))
        )
        target_field.resource = target_resource
        return struc.Reference(
            source=self.parse_field(
                graph, _only(graph.objects(parent, OEO.has_source))
            ),
            target=target_field,
        )

    def parse_review(self, graph: Graph, parent: Node) -> struc.Review:
        return struc.Review(
            badge=_one_str_or_none(graph.objects(parent, OEO.has_badge)),
            path=_one_str_or_none(graph.objects(parent, FOAF.page)),
        )

    def parse_meta_comment(self, graph: Graph, parent: Node) -> struc.MetaComment:
        return struc.MetaComment(
            dates=_one_str_or_none(graph.objects(parent, OEO.dates_info)),
            languages=_one_str_or_none(graph.objects(parent, OEO.languages_info)),
            licenses=_one_str_or_none(graph.objects(parent, OEO.licenses_info)),
            metadata_info=_one_str_or_none(graph.objects(parent, OEO.metadata_info)),
            none=_one_str_or_none(graph.objects(parent, OEO.none_info)),
            review=_one_str_or_none(graph.objects(parent, OEO.review_info)),
            units=_one_str_or_none(graph.objects(parent, OEO.units_info)),
        )

    def parse_metadata(self, graph: Graph, parent: Node) -> struc.OEPMetadata:
        context = self.parse_context(graph, parent)
        contributors = [
            self.parse_contributor(graph, c)
            for c in graph.objects(parent, OEO.has_contribution)
        ]
        language = [str(l) for l in graph.objects(parent, DCTERMS.language)]
        spatial = self.parse_spatial(
            graph, _only(graph.objects(parent, DCTERMS.spatial))
        )

        temporal = self.parse_temporal(
            graph, _only(graph.objects(parent, DCTERMS.temporal))
        )
        comment = self.parse_meta_comment(
            graph, _only(graph.objects(parent, OEO.comment))
        )
        resources = [
            self.parse_resource(graph, r)
            for r in graph.objects(parent, OEO.has_resource)
        ]
        terms_of_use = [
            self.parse_terms_of_use(graph, l)
            for l in graph.objects(parent, OEO.has_terms_of_use)
        ]
        sources = [
            self.parse_source(graph, s) for s in graph.objects(parent, DCTERMS.source)
        ]
        review = self.parse_review(graph, _only(graph.objects(parent, OEO.has_review)))
        return struc.OEPMetadata(
            comment=comment,
            context=context,
            contributions=contributors,
            description=_one_str_or_none(graph.objects(parent, DCTERMS.description)),
            identifier=str(parent),
            keywords=list(map(str, graph.objects(parent, DCAT.keyword))),
            languages=language,
            name=_one_str_or_none(graph.objects(parent, ADMS.Identifier)),
            terms_of_use=terms_of_use,
            publication_date=self.parse_date(
                _only(graph.objects(parent, OEO.publicationDate))
            ),
            resources=resources,
            review=review,
            sources=sources,
            spatial=spatial,
            temporal=temporal,
            title=_one_str_or_none(graph.objects(parent, DCTERMS.title)),
        )
