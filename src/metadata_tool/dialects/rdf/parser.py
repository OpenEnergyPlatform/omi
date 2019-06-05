from dateutil.parser import parse as parse_date
from rdflib import Graph
from rdflib.graph import Node
from rdflib.graph import URIRef
from rdflib.namespace import DCTERMS
from rdflib.namespace import FOAF
from rdflib.namespace import RDF
from rdflib.namespace import XSD

import metadata_tool.structure as struc
from metadata_tool.dialects.base.parser import Parser
from metadata_tool.dialects.rdf.namespace import ADMS
from metadata_tool.dialects.rdf.namespace import DCAT
from metadata_tool.dialects.rdf.namespace import DCATDE
from metadata_tool.dialects.rdf.namespace import OEO
from metadata_tool.dialects.rdf.namespace import SCHEMA
from metadata_tool.dialects.rdf.namespace import SKOS


def _only(gen):
    r = _one_or_none(gen)
    if r is None:
        raise Exception("No matching elements")
    return r


def _one_or_none(gen):
    l = list(gen)
    if not l:
        return None
    if len(l) > 1:
        raise Exception("Found more than one match")
    return l[0]

class RDFParser(Parser):
    def parse(self, inp: str, *args, **kwargs):
        g = Graph()
        g.parse(data=inp, format="ttl")
        for dataset in {s for s, _, _ in g}.difference({o for _, _, o in g}):
            return self.parse_metadata(g, dataset)

    def parse_date(self, node: Node):
        return parse_date(node)

    def parse_context(self, graph: Graph, parent: Node) -> struc.Context:
        return struc.Context(
            contact=str(_only(graph.objects(parent, DCAT.contactpoint))),
            documentation=str(_only(graph.objects(parent, OEO.documentation))),
            grant_number=str(_only(graph.objects(parent, OEO.grantNo))),
            homepage=str(_only(graph.objects(parent, FOAF.homepage))),
            source_code=str(_only(graph.objects(parent, OEO.sourceCode))),
        )

    def parse_contributor(self, graph: Graph, parent: Node) -> struc.Contributor:
        return struc.Contributor(
            contributor=self.parse_person(graph, _only(graph.objects(parent, DCTERMS.contributor))),
            date=self.parse_date(_only(graph.objects(parent, OEO.date))),
            obj=str(_only(graph.objects(parent, OEO.object))),
            comment=str(_only(graph.objects(parent, OEO.comment))),
        )

    def parse_person(self, graph, parent: Node):
        return struc.Person(
            name=str(_only(graph.objects(parent, FOAF.name))),
            email=str(_only(graph.objects(parent, FOAF.mbox))),
        )

    def parse_spatial(self, graph: Graph, parent: Node) -> struc.Spatial:
        return struc.Spatial(
            extent=str(_only(graph.objects(parent, SKOS.prefLabel))),
            location=str(_only(graph.objects(parent, OEO.location))),
            resolution=str(_only(graph.objects(parent, OEO.has_spatial_resolution))),
        )

    def parse_temporal(self, graph: Graph, parent: Node) -> struc.Temporal:
        return struc.Temporal(
            start=self.parse_date(_only(graph.objects(parent, SCHEMA.startDate))),
            end=self.parse_date(_only(graph.objects(parent, SCHEMA.endDate))),
            ts_orientation=struc.TimestampOrientation.create(str(_only(graph.objects(parent, OEO.has_orientation)))),
            reference_date=self.parse_date(
                _only(graph.objects(parent, OEO.referenceDate))
            ),
            resolution=str(_only(graph.objects(parent, OEO.has_time_resolution))),
        )

    def parse_source(self, graph: Graph, parent: Node) -> struc.Source:
        return struc.Source(
            title=str(_only(graph.objects(parent, DCTERMS.title))),
            description=str(_only(graph.objects(parent, DCTERMS.description))),
            path=str(_only(graph.objects(parent, FOAF.page))),
            source_license=_only(graph.objects(parent, DCTERMS.license)),
            source_copyright=str(_only(graph.objects(parent, DCTERMS.rights))),
        )

    def parse_license(self, graph: Graph, parent: Node) -> struc.License:
        if isinstance(parent, URIRef):
            return None
        else:
            return struc.License(
                attribution=str(_only(
                    graph.objects(parent, DCATDE.licenseAttributionByText)
                )),
                instruction=str(_only(graph.objects(parent, DCTERMS.title))),
                title=str(_only(graph.objects(parent, DCTERMS.title))),
                name=str(_only(graph.objects(parent, DCTERMS.title))),
                path=str(_only(graph.objects(parent, DCTERMS.title))),
            )

    def parse_resource(self, graph: Graph, parent: Node) -> struc.Resource:
        return struc.Resource(
            dialect=self.parse_dialect(graph, _only(graph.objects(parent, OEO.has_dialect))),
            encoding=str(_only(graph.objects(parent, OEO.encoding))),
            name=str(_only(graph.objects(parent, DCTERMS.title))),
            path=str(_only(graph.objects(parent, DCAT.accessURL))),
            profile=str(_only(graph.objects(parent, OEO.profile))),
            resource_format=str(_only(graph.objects(parent, OEO.has_format))),
            schema=self.parse_schema(graph, parent),
        )

    def parse_schema(self, graph: Graph, parent: Node) -> struc.Schema:
        return struc.Schema(
            fields=[
                self.parse_field(graph, f) for f in graph.objects(parent, OEO.field)
            ],
            primary_key=[f for f in graph.objects(parent, OEO.primaryKey)],
            foreign_keys=[
                self.parse_foreign_key(graph, f)
                for f in graph.objects(parent, OEO.has_foreignKey)
            ],
        )

    def parse_dialect(self, graph: Graph, parent: Node) -> struc.Dialect:
        delim = _one_or_none(graph.objects(parent, DCTERMS.delimiter))
        if delim is not None:
            delim = str(delim)
        return struc.Dialect(
            decimal_separator=str(_only(graph.objects(parent, OEO.decimalSeparator))),
            delimiter=delim,
        )

    def parse_field(self, graph: Graph, parent: Node) -> struc.Field:
        return struc.Field(
            name=str(_only(graph.objects(parent, DCTERMS.title))),
            unit=str(_only(graph.objects(parent, OEO.unit))),
            field_type=str(_only(graph.objects(parent, OEO.type))),
            description=str(_only(graph.objects(parent, DCTERMS.description))),
        )

    def parse_foreign_key(self, graph: Graph, parent: Node) -> struc.ForeignKey:
        return struc.ForeignKey(
            references=[self.parse_reference(graph, r) for r in graph.objects(parent, OEO.reference)])

    def parse_reference(self, graph: Graph, parent: Node) -> struc.Reference:
        return struc.Reference(
            source=self.parse_field(graph, _only(graph.objects(parent, OEO.has_source))),
            target=self.parse_field(graph, _only(graph.objects(parent, OEO.has_target)))
        )

    def parse_review(self, graph: Graph, parent: Node) -> struc.Review:
        return struc.Review(
            badge=str(_only(graph.objects(parent, OEO.has_badge))),
            path=str(_only(graph.objects(parent, FOAF.page))),
        )

    def parse_meta_comment(self, graph: Graph, parent: Node) -> struc.MetaComment:
        return struc.MetaComment(
            dates=str(_only(graph.objects(parent, OEO.dates_info))),
            languages=str(_only(graph.objects(parent, OEO.languages_info))),
            licenses=str(_only(graph.objects(parent, OEO.licenses_info))),
            metadata_info=str(_only(graph.objects(parent, OEO.metadata_info))),
            none=str(_only(graph.objects(parent, OEO.none_info))),
            review=str(_only(graph.objects(parent, OEO.review_info))),
            units=str(_only(graph.objects(parent, OEO.units_info))),
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
        licenses = [
            self.parse_license(graph, l) for l in graph.objects(parent, DCTERMS.license)
        ]
        sources = [
            self.parse_source(graph, s) for s in graph.objects(parent, DCTERMS.source)
        ]
        review = self.parse_review(graph, _only(graph.objects(parent, OEO.has_review)))
        return struc.OEPMetadata(
            comment=comment,
            context=context,
            contributors=contributors,
            description=str(_only(graph.objects(parent, DCTERMS.description))),
            identifier=str(parent),
            keywords=list(map(str, graph.objects(parent, DCAT.keyword))),
            languages=language,
            name=str(_only(graph.objects(parent, ADMS.Identifier))),
            object_licenses=licenses,
            publication_date=self.parse_date(
                _only(graph.objects(parent, OEO.publicationDate))
            ),
            resources=resources,
            review=review,
            sources=sources,
            spatial=spatial,
            temporal=temporal,
            title=str(_only(graph.objects(parent, DCTERMS.title))),
        )
