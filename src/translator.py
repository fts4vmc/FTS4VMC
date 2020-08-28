####################################
#             MTSv                 #
####################################

import sys
import pydot

import src.analyser
#From analyser we use:
#   function load_dot(path)
    
class Translator:
    __fts
    __mtsv

    def load_model(path):
        #path := path to DOT file
        try:
            __fts = src.load_dot(path)
        except Exception as e:
            print(str(e))
            sys.exit(0)

    def translate(self):
        if __fts == None:
            raise Exception('No model loaded!')
            return None
        self.__mtsv = ''
        
        #States
        #The set of states of the new MTSv is obtained from
        #the FTS's by adding a fresh state to it.
        q = self.__fts._states
        sink_state = State('sink state')
        q.add(sink_state)
        
        #Actions, May/Must transitions, Variability constraints
        #Those sets are obtained from the FTS as follows:
        sigma = {}
        delta_diamond = {}
        var_constr = {}
        for t in self.__fts._transitions:
            #Actions
            #For each transition (q,a,phi,q') in the FTS's transition relation
            #where " q,q' " are states, " a " is a label and " phi " is a feature 
            #symbol, add (a,phi) to the set
            sigma.add((t._label,t._constraint))
            #For each label " a " which does not appear in a transition, add " a "
            #to the set
            sigma.add(t._label)
            #For each feature symbol " phi ", add " phi " to the set
            sigma.add(t._constraint)
            
            #May transitions - part one
            #For each transition (q,a,phi,q') in the FTS's transition relation,
            #add (q,(a,phi),q') to the MTSv's may transition relation
            delta_diamond.add((t._in,(t._label,t._constraint)t._out))
            #not done yet: see the comment after the for

            #The Must transitions set is left empty

            #Variability constraints - part one
            #For each (q,a,phi,q') in the FTS's transition relation, add 
            # (a,phi) iff phi to the MTSv's variability constraints
            var_constr.add('(' + str(t._label) + ',' + str(t._constraint)  + ')' + ' IFF ' + str(t._constraint))
            

        #May transitions - part two
        #Let sigma_diff be the difference between the set of states of the
        #MTSv(sigma) and the set of states of the FTS, let q_start be the
        #initial state of the FTS, let s be the previously created sink state.
        #Then, for each symbol " sym " in sigma_diff, add (q_start,sym,s) to 
        #the MTSv's may transition relation
        with sigma - self.__fts._states as sigma_diff:
            for sym in sigma_diff:
                delta_diamod.add(self.__fts._initial,sym,sink_state)

        #Variability constraints - part two
        #Define a parser for the feature model
        from lark import Lark as lk
        fm_parser = lk(r"""
            formula: symbol op formula
                   | symbol
            op: and
              | or
              | =>
              | <=>
              | xor

            symbol: WORD

            %import common.WORD

            """, start = 'formula'
        )
        tree = fm_parser.parse(self.__fts._fm)#Parse the feature model
