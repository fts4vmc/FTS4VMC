#########################################################
#             Translate to VMC's format                 #
#########################################################

import sys
import pydot
import os
import re
import traceback
import src.internals.analyser as analyser

class Translator:
    __slots__= '__fts', 'output', '_mts'


    def __init__(self):
        self.output = ''

    def load_model(self,path):
        #path := path to DOT file
        try:
            self.__fts = analyser.load_dot(open(path,"r"))
        except Exception as e:
            traceback.print_exc()
            sys.exit(0)

    def translate(self):
        if self.__fts == None:
            raise Exception('No model loaded!')
            return None
        self.output = ''
        initial_state = 'SYS = C' + str(self.__fts._initial._id)#The initial state is the same
        adj = {}#Dictionary used to map the id of a state to it's "adjacency list"
        single_transition = {}#map (state,boolean_var) | boolean_var = true iff state has only one transition
        for t in self.__fts._transitions:
            id = str(t._in._id)
            if id not in adj:
                if len(self.__fts._states[id]._out) > 1:
                    tmp = 'C' + id + ' = ' + str(t._label) + '(may).' + 'C' + str(t._out._id)
                else:
                    tmp = 'C' + id + ' = ' + str(t._label) + '.C' + str(t._out._id)
                adj.update([(id,tmp)])
            else:
                adj[id] += ' + ' + str(t._label) + '(may).' + 'C' + str(t._out._id)
        for a in adj:
            self.output += adj[a] + '\n'
        self.output += '\n' + initial_state + '\n\nConstraints{ LIVE }'

    def get_output(self):
        if self.output != '':
            return self.output
        else: return 'Nothing to show: No translation has occurred'

    def load_mts(self,mts):
        self._mts = mts

    def mts_to_dot(self,out_file):
        if self._mts == None:
            return 'Nothing to show: No translation has occurred'
        dot = pydot.Dot()
        edges = dict()
        mts_lines = self._mts.split('\n')
        for line in mts_lines[:len(mts_lines)-1]:
            if line != "\n":
                print("line:")
                print(line)
                state, edges_line = line.split('-->')
                state_num_str = re.findall(r'\d+', state)
                state_num = int(state_num_str[0])
                state_num_str2, rest = (edges_line[:len(edges_line)-1]).split('{')
                state_num_str2 = re.findall(r'\d+', state_num_str2)
                state_num_2 = int(state_num_str[0])  
                tmp_list = rest.split(', ')
                if(len(tmp_list) == 2):#may, <something>
                    mode, feature = rest.split(', ')
                    label = mode + ' | ' + feature
                else:#<something>
                    label = rest
                new_edge = pydot.Edge(state_num_str[0],state_num_str2[0])
                new_edge.obj_dict['attributes']['label'] = label 
                dot.add_edge(new_edge)
                print(dot.to_string())
        svg_graph = dot.create_svg()
        if out_file:
            with open(out_file,'wb') as of:
                of.write(svg_graph)
