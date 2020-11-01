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

    def test_vending_new(self, vendingnew):
        import os
        t = Translator()
        t.load_model(vendingnew)
        t.translate()
        with open(os.path.join('tests', 'vmc', 'vendingnew-vmc-test.txt')) as result:
            assert t.get_output()+'\n' == result.read()

    def test_translation(self, tmp_path):
        import os
        import src.internals.analyser as analyser
        from src.internals.disambiguator import Disambiguator
        from src.internals.vmc_controller import VmcController
        dot = os.listdir(os.path.join('tests','dot'))
        with open(os.path.join(tmp_path, "true.txt"), 'w') as true:
            true.write("[true] true")
        true = open(os.path.join(tmp_path, "true.txt"), 'r')
        for source in dot:
            with open(os.path.join('tests','dot', source), 'r') as fts_source:
                fts = analyser.load_dot(fts_source)
            fts_source.close()
            analyser.z3_analyse_full(fts)
            dis = Disambiguator.from_file(os.path.join('tests', 'dot', source))
            dis.remove_transitions(fts._set_dead)
            dis.set_true_list(fts._set_false_optional)
            dis.solve_hidden_deadlocks(fts._set_hidden_deadlock)
            with open(os.path.join(tmp_path, "fixed-"+source), 'w') as out:
                out.write(dis.get_graph())
            t = Translator()
            t.load_model(os.path.join(tmp_path, "fixed-"+source))
            t.translate()
            with open(os.path.join(tmp_path, "vmc-"+source), 'w') as out:
                out.write(t.get_output())
            vmc = VmcController("./vmc65-linux")
            vmc.run_vmc(os.path.join(tmp_path, "vmc-"+source), os.path.join(tmp_path, "true.txt"))
            assert vmc.get_eval() == "TRUE"
        true.close()
