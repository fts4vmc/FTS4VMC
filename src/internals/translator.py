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
        print(self._vmc_to_analyser)
        print(self._analyser_to_vmc)
        return self._vmc_to_analyser[vmc_state]

    def contains_analyser_id(self,id):
        return self._analyser_to_vmc[id]

    def contains_vmc_id(self,id):
        return self._vmc_to_analyser[id]

    def get_vmc_states(self):
        return list(self._vmc_to_analyser.keys())

class Translator:
    __slots__= '__fts', 'output', '_mts', '__id_map'

    def __init__(self):
        self.output = ''
        #This map is the most important one since it will hold the correspondence
        #between the analyser states' names and the vmc states' ones
        self.__id_map = DoubleMap()

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
                
        
        #Used in the following for cycle to determine the current state's
        #name when inserted into the MTS
        last_state_num = 0

        for t in self.__fts._transitions:
            id = str(t._in._id)
            tmp_state_id = last_state_num + 1
            if(self.__id_map.add_states(id,'C' + str(tmp_state_id)) == True):
                last_state_num += 1
                
            analyser_id = id #analyser id preserved(it is required below)
            id = self.__id_map.analyser_to_vmc(id)
            #Check if the state is the initial one
            if(t._in._id == self.__fts._initial._id):
                self.__id_map.add_states(self.__fts._initial._id, 'C0')
                initial_state = 'SYS = ' + id

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
            if(self.__id_map.add_states(dest_id,'C' + str(tmp_state_id))):
                last_state_num += 1

            dest_id = self.__id_map.analyser_to_vmc(dest_id)

            if self.__id_map.analyser_to_vmc(analyser_id) not in adj:
                print(analyser_id)
                print(adj)
                if len(self.__fts._states[analyser_id]._out) > 1:
                    tmp = id + ' = ' + label + '(may).' + dest_id
                else:
                    tmp = id + ' = ' + label + '.' + dest_id
                adj.update([(id,tmp)])
            else:
                print('updated')
                adj[id] += ' + ' + label  + '(may).' + dest_id
                print(adj[id])

        for s in self.__id_map.get_vmc_states():
            if(s in adj):
                self.output += adj[s] + '\n'
            else:
                self.output += s + ' = dead.nil\n'
        self.output += '\n' + initial_state + '\n\nConstraints{ LIVE }'
        print(self.output)
        print(self.__id_map)

    def get_output(self):
        if self.output != '':
            return self.output
        else: return 'Nothing to show: No translation has occurred'

    #The following methods are used to load an mts and to translate it into dot
    #format. Required in order to being able to display the counterexample graph
    def load_mts(self,mts):
        self._mts = mts

    def mts_to_dot(self,out_file):
        print(self.__id_map)
        if self._mts == None:
            return 'Nothing to show: No translation has occurred'
        dot = pydot.Dot()
        edges = dict()
        mts_lines = self._mts.split('\n')
        for line in mts_lines[:len(mts_lines)-1]:
            if line != "\n":
                state, edges_line = line.split('-->')
                state = state.replace(" ","")
                state_num = self.__id_map.vmc_to_analyser(state)

                state2, rest = (edges_line[:len(edges_line)-1]).split('{')
                state2 = state2.replace(" ","")
                state_num_2 = self.__id_map.vmc_to_analyser(state2)
                tmp_list = rest.split(', ')
                if(len(tmp_list) == 2):#may, <something>
                    action, feature = rest.split(', ')
                    label = action + ' | ' + feature
                else:#<something>
                    label = rest
                new_edge = pydot.Edge(state_num,state_num_2)
                new_edge.obj_dict['attributes']['label'] = label 
                dot.add_edge(new_edge)
        svg_graph = dot.create_svg()
        if out_file:
            with open(out_file,'wb') as of:
                of.write(svg_graph)
