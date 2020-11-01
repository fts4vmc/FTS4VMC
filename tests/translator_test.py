import pytest
from src.internals.translator import Translator

class TestTranslator:
    @pytest.fixture
    def vendingnew(self, tmp_path):
        import os
        import src.internals.analyser as analyser
        from src.internals.disambiguator import Disambiguator
        dis = Disambiguator.from_file(os.path.join('tests', 'dot', 'vendingnew.dot'))
        with open(os.path.join('tests','dot', 'vendingnew.dot'), 'r') as fts_source:
            fts = analyser.load_dot(fts_source)
        fts_source.close()
        analyser.z3_analyse_full(fts)
        dis = Disambiguator.from_file(os.path.join('tests', 'dot', 'vendingnew.dot'))
        dis.remove_transitions(fts._set_dead)
        dis.set_true_list(fts._set_false_optional)
        dis.solve_hidden_deadlocks(fts._set_hidden_deadlock)
        with open(os.path.join(tmp_path, "fixed-vendingnew.dot"), 'w') as out:
            out.write(dis.get_graph())
        return os.path.join(tmp_path, 'fixed-vendingnew.dot')

    @pytest.fixture
    def true(self, tmp_path):
        import os
        with open(os.path.join(tmp_path, "true.txt"), 'w') as true:
            true.write("[true] true")
        return os.path.join(tmp_path, "true.txt")

    @pytest.fixture
    def fixed_dot(self, tmp_path):
        import os
        import src.internals.analyser as analyser
        from src.internals.disambiguator import Disambiguator
        dots = []
        dot = os.listdir(os.path.join('tests','dot'))
        for source in dot:
            with open(os.path.join('tests','dot', source), 'r') as fts_source:
                fts = analyser.load_dot(fts_source)
            fts_source.close()
            analyser.z3_analyse_full(fts)
            dis = Disambiguator.from_file(os.path.join('tests', 'dot', source))
            dis.remove_transitions(fts._set_dead)
            dis.set_true_list(fts._set_false_optional)
            dis.solve_hidden_deadlocks(fts._set_hidden_deadlock)
            dots.append(os.path.join(tmp_path, "fixed-"+source))
            with open(os.path.join(tmp_path, "fixed-"+source), 'w') as out:
                out.write(dis.get_graph())
        return dots

    def test_vending_new(self, vendingnew):
        import os
        t = Translator()
        t.load_model(vendingnew)
        t.translate()
        with open(os.path.join('tests', 'vmc', 'vendingnew-vmc-test.txt')) as result:
            assert t.get_output()+'\n' == result.read()

    def test_translation(self, tmp_path, fixed_dot, true):
        import os
        from src.internals.vmc_controller import VmcController
        for source in fixed_dot:
            t = Translator()
            t.load_model(source)
            t.translate()
            path, dot = os.path.split(source)
            path = os.path.join(path, 'vmc-'+dot)
            with open(path, 'w') as out:
                out.write(t.get_output())
            vmc = VmcController("./vmc65-linux")
            vmc.run_vmc(path, true)
            assert vmc.get_eval() == "TRUE"
