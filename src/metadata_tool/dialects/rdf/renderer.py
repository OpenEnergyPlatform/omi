from metadata_tool.dialects.base.renderer import Renderer
from rdflib.graph import Graph


class GraphRenderer(Renderer):
    def render(self, inp: Graph, *args, **kwargs):
        return inp.serialize(format="ttl")
