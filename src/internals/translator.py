#########################################################
#             Translate to VMC's format                 #
#########################################################

import sys
import pydot
import os
import re
import traceback
import src.internals.analyser as analyser

class DoubleMap:
    __slots__ = '_analyser_to_vmc', '_vmc_to_analyser'

    def __init__(self):
        self._analyser_to_vmc = {}
        self._vmc_to_analyser = {}

    def add_states(self,analyser_state,vmc_state):
        if(not (analyser_state in self._analyser_to_vmc)):
            self._analyser_to_vmc.update([(analyser_state, vmc_state)])
            self._vmc_to_analyser.update([(vmc_state, analyser_state)])
            return True
        else:
            return False

    def analyser_to_vmc(self,analyser_state):
        return self._analyser_to_vmc[analyser_state]

    def vmc_to_analyser(self,vmc_state):
        return self._vmc_to_analyser[vmc_state]

    def contains_analyser_id(self,id):
        return self._analyser_to_vmc[id]

    def contains_vmc_id(self,id):
        return self._vmc_to_analyser[id]
    def get_vmc_states(self):
        return list(self._vmc_to_analyser.keys())

class Translator:
    __slots__= '__fts', 'output', '_mts', '_id_map'


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
        #Dictionary used to map the id of a state to it's "adjacency list"
        adj = {}
        #map (state,boolean_var) | boolean_var = true iff state has only one
        #transition
        single_transition = {}
        #This map is the most important one since it will hold the correspondence
        #between the analyser's states and the vmc's ones
        self._id_map = DoubleMap()
        
        
        self._id_map.add_states(self.__fts._initial._id, 'C0') 
        initial_state = 'SYS = C0'#The initial state is the same
        last_state_num = -1

        for t in self.__fts._transitions:
            id = str(t._in._id)
            tmp_state_id = last_state_num + 1
            if(self._id_map.add_states(id,'C' + str(tmp_state_id)) == True):
                last_state_num += 1
                
            analyser_id = id #analyser id preserved(it is required below)
            id = self._id_map.analyser_to_vmc(id)
            
            label = str(t._label)
            unlabeled = label.find('-')
            if unlabeled >= 0:
                l_pt1 = label[:unlabeled]
                l_pt2 = label[unlabeled+1:]
                label = l_pt1 + '_unlabeled_' + l_pt2
            
            open_br = label.find('(')
            if open_br >= 0:
                l_pt1 = label[:open_br]
                l_pt2 = label[open_br+1:]
                label = l_pt1 + l_pt2

            close_br = label.find(')')
            if close_br >= 0:
                l_pt1 = label[:close_br]
                l_pt2 = label[close_br+1:]
                label = l_pt1 + l_pt2

            dest_id = str(t._out._id)#Will hold the destination state
            tmp_state_id = last_state_num + 1
            if(self._id_map.add_states(dest_id,'C' + str(tmp_state_id))):
                last_state_num += 1

            dest_id = self._id_map.analyser_to_vmc(dest_id)

            if analyser_id not in adj:
                if len(self.__fts._states[analyser_id]._out) > 1:
                    tmp = id + ' = ' + label + '(may).' + dest_id
                else:
                    tmp = id + ' = ' + label + '.' + dest_id
                adj.update([(id,tmp)])
            else:
                adj[id] += ' + ' + label  + '(may).' + dest_id

        for s in self._id_map.get_vmc_states():
            if(s in adj):
                self.output += adj[s] + '\n'
            else:
                self.output += s + ' = dead.nil\n'
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
                state, edges_line = line.split('-->')
                state_num_str = re.findall(r'\d+', state)
                state_num = int(state_num_str[0])
                state_num_str2, rest = (edges_line[:len(edges_line)-1]).split('{')
                state_num_str2 = re.findall(r'\d+', state_num_str2)
                state_num_2 = int(state_num_str[0])  
                tmp_list = rest.split(', ')
                if(len(tmp_list) == 2):#may, <something>
                    action, feature = rest.split(', ')
                    label = action + ' | ' + feature
                else:#<something>
                    label = rest
                new_edge = pydot.Edge(state_num_str[0],state_num_str2[0])
                new_edge.obj_dict['attributes']['label'] = label 
                dot.add_edge(new_edge)
        svg_graph = dot.create_svg()
        if out_file:
            with open(out_file,'wb') as of:
                of.write(svg_graph)
