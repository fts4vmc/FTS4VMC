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
    __slots__= '__fts', '__mtsv'

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
        self.__mtsv = ''
        start = 'SYS = C'
        adj = {}#Dictionary used to register the adjacencies  
        for t in self.__fts._transitions:
            if(t._in._id == self.__fts._initial):
                start += str(t._in._id)
            id = str(t._in._id)
            if id not in adj:
                tmp = 'C' + id + ' = ' + str(t._label) + '(may).' + 'C' + str(t._out._id)
                adj.update([(id,tmp)])
            else:
                adj[id] += ' + ' + str(t._label) + '(may).' + 'C' + str(t._out._id)
        for a in adj:
            self.__mtsv += adj[a] + '\n'
        self.__mtsv += '\n' + start + '\n\nConstraints{ LIVE }'

    def get_mtsv(self):
        if self.__mtsv != None:
            return self.__mtsv
        else: return 'No model loaded'
###########################FOR TESTING PURPOSES ONLY#################
import sys

def main():
    t = Translator()
    t.load_model(sys.argv[1])
    t.translate()
    print(t.get_mtsv())

if __name__ == '__main__':
    main()
