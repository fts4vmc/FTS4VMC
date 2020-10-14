import pytest
from src.internals.disambiguator import Disambiguator

class TestDisambiguator:
    @pytest.fixture
    def graph(self):
        import os
        dis = Disambiguator.from_file(os.path.join('tests', 'ambiguous.dot'))
        return dis

    @pytest.fixture
    def disambiguated_graph(self):
        import os
        dis = Disambiguator.from_file(os.path.join('tests', 'test_fts_disambiguato.dot'))
        return dis

    def test_remove_transition(self, graph):
        dis = graph
        dis.remove_transition('C2', 'C2', 'a', 'f2')
        assert dis._Disambiguator__fts.get_edge('C2', 'C2') == []

    def test_set_true(self, graph):
        dis = graph
        dis.set_true('C2', 'C3', 'a', 'f1')
        assert dis._Disambiguator__fts.get_edge('C2', 'C3')[0].get_label(
                ).split('|')[-1].strip() == 'True'

    def test_solve_hidden_deadlock(self, graph):
        dis = graph
        dis.solve_hidden_deadlock('C1', 'DEAD')
        dead_tr = dis._Disambiguator__fts.get_edge('C1', 'DEAD')[0]
        assert (dead_tr.get_source() == 'C1' and 
                dead_tr.get_destination() == 'DEAD' and
                dead_tr.get_label() == 'DEAD | not ( f1)')

    def test_highlight(self, graph):
        dis = graph
        dead = [{'src': 'C2', 'dst':'C2', 'label':'a', 'constraint':'f2'}]
        false = [{'src': 'C2', 'dst':'C3', 'label':'a', 'constraint':'f1'}]
        hidden = ['C1']
        dis.highlight_ambiguities(dead, false, hidden)
        dead_tr = dis._Disambiguator__fts.get_edge('C2', 'C2')[0]
        false_tr = dis._Disambiguator__fts.get_edge('C2', 'C3')[0]
        hidden_st = dis._Disambiguator__fts.get_node('C1')[0]
        assert (dead_tr.get_color() == 'blue' and 
            false_tr.get_color() == 'green' and 
            hidden_st.get_fillcolor() == 'red')

