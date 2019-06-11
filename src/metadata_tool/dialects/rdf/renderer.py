from metadata_tool.dialects.base.renderer import Renderer
from rdflib.graph import Node


class GraphRenderer(Renderer):
    def render(self, inp: Node, *args, **kwargs):
        return inp.serialize(format="ttl")
