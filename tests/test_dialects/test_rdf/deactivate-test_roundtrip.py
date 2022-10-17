from rdflib import Graph
from rdflib.compare import _squashed_graphs_triples
from rdflib.compare import isomorphic

from omi.dialects.oep.compiler import JSONCompiler
from omi.dialects.oep.parser import JSONParser_1_4
from omi.dialects.oep.renderer import JSONRenderer
from omi.dialects.rdf.compiler import RDFCompiler
from omi.dialects.rdf.parser import RDFParser


def test_roundtrip():
    json_compiler = JSONCompiler()
    json_parser = JSONParser_1_4()
    json_renderer = JSONRenderer()
    rdf_compiler = RDFCompiler()
    rdf_p = RDFParser()
    with open("tests/data/metadata_v14.ttl", "r") as _input_file:
        input_string = _input_file.read()
        expected_graph = Graph()
        expected_graph.parse(data=input_string, format="ttl")
        # Step 1: Parse Turtle to internal structure
        internal_metadata = rdf_p.parse_from_string(input_string)
        # Step 2: Translate to json string
        json_metadata = json_renderer.render(json_compiler.visit(internal_metadata))
        # Step 3: Parse json string
        internal_metadata2 = json_parser.parse_from_string(json_metadata)
        # Step 4: Translate to Turtle
        _ = rdf_compiler.visit(internal_metadata2)
        # Final step: Compare
        for (t1, t2) in _squashed_graphs_triples(expected_graph, rdf_compiler.graph):
            assert t1 == t2
        assert isomorphic(expected_graph, rdf_compiler.graph)
