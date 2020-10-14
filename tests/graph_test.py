import pytest
from src.internals.graph import Graph

class TestGraph():

    @pytest.fixture
    def graph(self):
        import os
        source = Graph.from_file(os.path.join('tests', 'test_fts_disambiguato.dot'))
        return source

    def test_draw_graph(self, graph, tmp_path):
        d = tmp_path / "draw_graph"
        d.mkdir()
        p = d / "test.svg"
        graph.draw_graph(str(p.resolve()))
        assert  str(graph._Graph__graph.create_svg()).find(p.read_text())

    def test_get_graph_number(self, graph):
        edge, node = graph.get_graph_number()
        assert edge == 5 and node == 5
