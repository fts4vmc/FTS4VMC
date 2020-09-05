import pydot
import string
import random
from analyser import c_translator

class Disambiguator(object):

    __slots__ = '__fts', '__ctran'

    def __init__(self, filename):
        self.__fts = pydot.graph_from_dot_file(filename)[0]
        self.__ctran = c_translator()

    def remove_transition(self, src, dst, label, constraint):
        transition_list = self.__fts.get_edge(src, dst)
        for index, transition in enumerate(transition_list):
            tmp = transition.obj_dict['attributes']['label'][1:-1].split('|')
            if label == tmp[0] and constraint == str(self.__ctran.c_translate(tmp[-1])):
                self.__fts.del_edge(src, dst, index)

    def remove_transitions(self, transition_list):
        for transition in transition_list:
            self.remove_transition(transition['src'], transition['dst'],
                    transition['label'], transition['constraint'])

    def set_true(self, src, dst, label, constraint):
        transition_list = self.__fts.get_edge(src, dst)
        for transition in transition_list:
            tmp = transition.obj_dict['attributes']['label'][1:-1].split('|')
            if label == tmp[0] and constraint == str(self.__ctran.c_translate(tmp[-1])):
                transition.obj_dict['attributes']['label'] = label + " | True"

    def set_true_list(self, transition_list):
        for transition in transition_list:
            self.set_true(transition['src'], transition['dst'],
                    transition['label'], transition['constraint'])

    def solve_hidden_deadlock(self, state, dead_state):
        if dead_state is None:
            dead_state = 'DEAD' + ''.join(random.sample(string.digits, 10))
            #self.__fts.add_node(pydot.Node(dead_state))
        transition_list = self.__fts.get_edges()
        tmp = []
        for transition in transition_list:
            if transition.get_source() == state:
                tmp.append('not (' + transition.obj_dict['attributes']['label'][1:-1].split('|')[-1] + ')')
        tmp_label = dead_state + " | " + " or ".join(tmp)
        print(state+", "+dead_state+", "+tmp_label)
        self.__fts.add_edge(pydot.Edge(src=state, dst=dead_state, obj_dict=None, label=tmp_label))

    def solve_hidden_deadlocks(self, state_list):
        if state_list:
            dead_state = 'DEAD' + ''.join(random.sample(string.digits, 10))
            #self.__fts.add_node(pydot.Node(dead_state))
            for state in state_list:
                self.solve_hidden_deadlock(state, dead_state)

    def remove_ambiguities(self, dead_tr, false_opt, hidden):
        self.remove_transitions(dead_tr)
        self.set_true_list(false_opt)
        self.solve_hidden_deadlocks(hidden)

    def get_graph(self):
        return self.__fts.to_string()
