#########################################################
#             Translate to VMC's format                 #
#########################################################

import sys
import pydot
import traceback

import src.analyser as analyser
#From analyser we use:
#   function load_dot(path)

class Translator:
    __slots__= '__fts', 'output'


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
###########################FOR TESTING PURPOSES ONLY#################
import sys

def main():
    t = Translator()
    t.load_model(sys.argv[1])
    t.translate()
    print(t.get_output())

if __name__ == '__main__':
    main()
