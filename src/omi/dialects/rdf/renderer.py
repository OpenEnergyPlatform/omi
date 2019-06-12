from rdflib.graph import Graph

from omi.dialects.base.renderer import Renderer


class GraphRenderer(Renderer):
    def render(self, inp: Graph, *args, **kwargs):
        return inp.serialize(format="ttl")
