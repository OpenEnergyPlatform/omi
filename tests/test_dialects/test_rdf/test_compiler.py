from rdflib import BNode
from rdflib import Graph
from rdflib.compare import _squashed_graphs_triples
from rdflib.compare import graph_diff
from rdflib.compare import isomorphic
from rdflib.compare import similar
from rdflib.compare import to_isomorphic

from omi.dialects.rdf.compiler import RDFCompiler

from ..internal_structures import metadata_v_1_4


def test_compiler_v1_4():
    compiler = RDFCompiler()
    with open("tests/data/metadata_v14.ttl", "r") as _input_file:
        expected_graph = Graph()
        expected_graph.parse(data=_input_file.read(), format="ttl")
        _ = compiler.visit(metadata_v_1_4)
        expected = to_isomorphic(expected_graph)
        got = to_isomorphic(compiler.graph)
        for (t1, t2) in _squashed_graphs_triples(expected, got):
            assert t1 == t2
        assert isomorphic(expected, got)
