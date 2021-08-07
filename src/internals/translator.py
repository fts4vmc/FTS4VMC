import sys
import pydot
import os
import traceback
import src.internals.analyser as analyser

class Translator:
    __slots__= '__fts', 'output', '_mts'

    def __init__(self):
        self.output = ''

    def load_model(self, path):
        try:
            file = open(path, "r")
            self.__fts = analyser.load_dot(file)
        except Exception as e:
            raise Exception('Invalid FTS file')
        finally:
            file.close()

    def get_id(self, state):
        if len(state._out._out) == 0:
            return 'nil'
        return str(state._out).strip()

    def sanitize_label(self, label):
        if label == None or label.strip() == '':
            label = 'tau'
        label = label.strip()
        if label == '-':
            label = 'tau'
        label = label.replace('(','_')
        label = label.replace(')','_')
        return label

    def translate(self):
        if self.__fts == None:
            raise Exception('No model loaded!')
            return None
        self.output = ''
        for k, s in self.__fts._states.items():
            line = ''
            if len(s._out) > 0:
                s._id = s._id.strip()
                line = s._id + ' = '
                sout = list(s._out)
                sout.sort(key=str)
                for t in sout:
                    if str(t._constraint).lower() == 'true':
                        line = line + self.sanitize_label(t._label) + '(must).' 
                        line = line + self.get_id(t) + ' +\n\t'
                    else:
                        line = line + self.sanitize_label(t._label) + '(may).' 
                        line = line + self.get_id(t) + ' +\n\t'
                line = line.strip()[:-2]+'\n'
                self.output += line + '\n'
        self.output += '\nSYS = ' + self.__fts._initial._id + '\n\nConstraints { LIVE }\n'

    def get_output(self):
        if self.output != '':
            return self.output
        else: return 'Nothing to show: No translation has occurred'

    #The following methods are used to load an mts and to translate it into dot
    #format. Required in order to being able to display the counterexample graph
    def load_mts(self, mts):
        self._mts = mts

    def mts_to_dot(self, out_file):
        optional = False
        if self._mts == None:
            return 'Nothing to show: No translation has occurred'
        dot = pydot.Dot()
        edges = dict()
        mts_lines = self._mts.split('\n')
        for line in mts_lines[:len(mts_lines)-1]:
            if line != "\n":
                state, edges_line = line.split('-->')
                state = state.strip()
                state2, rest = (edges_line[:len(edges_line)-1]).split('{')
                state2 = state2.strip()
                tmp_list = rest.split(', ')
                if(len(tmp_list) == 2):#may, <something>
                    t1, t2 = rest.split(', ')
                    if t1.strip() == 'may':
                        label = t2.strip()
                    else:
                        label = t1.strip()
                else:#<something>
                    label = rest
                new_edge = pydot.Edge(state, state2)
                new_edge.obj_dict['attributes']['label'] = label 
                dot.add_edge(new_edge)
        svg_graph = dot.create_svg()
        if out_file:
            with open(out_file,'wb') as of:
                of.write(svg_graph)
                of.flush()
