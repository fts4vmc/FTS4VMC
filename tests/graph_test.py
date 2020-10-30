import pytest
from src.internals.graph import Graph

class TestGraph():

    @pytest.fixture
    def graph(self):
        import os
        source = Graph.from_file(os.path.join('tests', 'dot', 'test_fts_disambiguato.dot'))
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

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Graph.from_file('nothing')

    def test_wrong_file_type(self):
        import os
        with pytest.raises(Exception, match=r"Wrong file format"):
            Graph.from_file(os.path.join('src', 'static', 'js', 'script.js'))

    def test_wrong_data_type(self):
        import os
        with pytest.raises(Exception, match=r"Invalid data"):
            with open(os.path.join('src','templates', 'main.html')) as source:
                Graph(source.read())

    def test_permission_error(self, graph):
        import os
        with pytest.raises(PermissionError):
            graph.draw_graph(os.path.join("/","test.svg"))
