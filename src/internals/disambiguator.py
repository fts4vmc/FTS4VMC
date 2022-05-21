import pydot
import puremagic
from src.internals.analyser import c_translator, Transition, State

class Disambiguator(object):
    """
    The Disambiguator class provides methods to remove ambiguities from
    featured transition systems
    """

    __slots__ = '__fts', '__ctran', '__dead_name'

    def __init__(self, data, name = 'DEAD'):
        try:
            self.__fts = pydot.graph_from_dot_data(data)[0]
        except:
            raise Exception("Invalid data")
        #Force Tob to Bottom view to improve readbility on browser page
        self.__fts.obj_dict['attributes']['rankdir'] = 'TB'
        self.__ctran = c_translator()
        self.__dead_name = name

    @classmethod
    def from_file(self, file_path, name = 'DEAD'):
        with open(file_path, 'r') as source:
            try:
                if puremagic.from_file(file_path) != '.dot':
                    raise Exception('Wrong file format')
                    return None
            except:
                raise Exception('Wrong file format')
                return None
            data = source.read()
            return self(data, name)

    def remove_transition(self, src, dst, label, constraint):
        """Remove the specified transition from the loaded fts model

        Arguments:
        src -- the source state name
        dst -- the destination state name
        label --  the target transition's label
        constraint -- the target transition's constraint formula,
            using the notation given by analyser.c_translator
        """
        if not (src and dst and label and constraint):
            return
        transition_list = self.__fts.get_edge(src, dst)
        for index, transition in enumerate(transition_list):
            if 'label' not in transition.obj_dict['attributes']:
                continue
            tmp = transition.obj_dict['attributes']['label'][1:-1].split('|')
            if label.strip() == tmp[0].strip() and constraint == str(self.__ctran.c_translate(tmp[-1])):
                self.__fts.del_edge(src, dst, index)

    def remove_transitions(self, transition_list):
        """Remove the transitions inside transition_list from the loaded fts model

        Arguments:
        transition_list -- list of transition to be removed expressed using the
            format compatible with remove_transition or instance of 
            analyser.Transition
        """
        for transition in transition_list:
            if isinstance(transition, Transition):
                self.remove_transition(transition._in._id, transition._out._id,
                        str(transition._label), str(transition._constraint))
            elif ('src' in transition and 'dst' in transition and
                    'label' in transition and 'constraint' in transition):
                self.remove_transition(transition['src'], transition['dst'],
                        transition['label'], transition['constraint'])

    def set_true(self, src, dst, label, constraint):
        """Set the transition's constraint formula to true

        Arguments:
        src -- the source state name
        dst -- the destination state name
        label --  the target transition's label
        constraint -- the target transition's constraint formula,
            using the notation given by analyser.c_translator
        """
        if not (src and dst and label and constraint):
            return
        transition_list = self.__fts.get_edge(src, dst)
        for transition in transition_list:
            if 'label' not in transition.obj_dict['attributes']:
                continue
            tmp = transition.obj_dict['attributes']['label'][1:-1].split('|')
            if label.strip() == tmp[0].strip() and constraint == str(
                    self.__ctran.c_translate(tmp[-1])):
                transition.obj_dict['attributes']['label'] = label + " | True"

    def set_true_list(self, transition_list):
        """Set the transitions' inside transition_list formulas to True

        Arguments:
        transition_list -- list of transition expressed using the format 
            compatible with set_true
        """
        for transition in transition_list:
            if isinstance(transition, Transition):
                self.set_true(transition._in._id, transition._out._id,
                        str(transition._label), str(transition._constraint))
            elif ('src' in transition and 'dst' in transition and
                    'label' in transition and 'constraint' in transition):
                self.set_true(transition['src'], transition['dst'],
                        transition['label'], transition['constraint'])

    def solve_hidden_deadlock(self, state, dead_state):
        """Make hidden deadlock explicit

        Arguments:
        state -- the hidden deadlock state name
        dead_state -- the deadlock state name
        """
        if not (state and dead_state):
            return
        if not self._still_hidden_deadlock(state):
            return
        #If transition between state and dead_state already exists do nothing
        if self.__fts.get_edge(state, dead_state):
            return
        transition_list = self.__fts.get_edges()
        tmp = []
        #Create feature expression of transition to dead_state
        for transition in transition_list:
            if (transition.get_source() == state and
                    'label' in transition.obj_dict['attributes']):
                tmp.append(transition.obj_dict['attributes']['label'][1:-1].split('|')[-1].strip())
        tmp_label = dead_state + " | not(" + " or ".join(tmp)+")"
        self.__fts.add_edge(pydot.Edge(src=state, dst=dead_state, obj_dict=None, label=tmp_label))

    def solve_hidden_deadlocks(self, state_list):
        """Make hidden deadlocks inside stale_list explicit

        Arguments:
        state_list -- list of states
        """
        if state_list:
            for state in state_list:
                if isinstance(state, State):
                    self.solve_hidden_deadlock(state._id, self.__dead_name)
                else:
                    self.solve_hidden_deadlock(state, self.__dead_name)

    def _still_hidden_deadlock(self, state):
        """Return True if state is the source of any transitions False otherwise

        It is used to check if the removal of dead transitions also solved
        hidden deadlock.
        """
        transitions = self.__fts.get_edges()
        for transition in transitions:
            if transition.get_source() == state:
                return True
        return False

    def __set_color(self, transition_list, color):
        """Updates transition style by changing color and applying bold style
        for the matching transition, contained in transition list."""
        for transition in transition_list:
            if not ('src' in transition and 'dst' in transition and
                    'label' in transition and 'constraint' in transition):
                continue
            edge_list = self.__fts.get_edge(transition['src'], transition['dst'])
            for edge in edge_list:
                if 'label' not in edge.obj_dict['attributes']:
                    continue
                tmp = edge.obj_dict['attributes']['label'][1:-1].split('|')
                if (transition['label'].strip() == tmp[0].strip() and
                        transition['constraint'] == str(self.__ctran.c_translate(tmp[-1]))):
                    edge.obj_dict['attributes']['color'] = color
                    edge.obj_dict['attributes']['style'] = 'bold'
                    edge.obj_dict['attributes']['fontcolor'] = color


    def highlight_ambiguities(self, dead =[], false =[], hidden=[]):
        """Given list containing ambiguities it updates the style on the graph
        changing the color of the matched element"""
        self.__set_color(dead, "blue")
        self.__set_color(false, "green")

        for state in hidden:
            self.__fts.add_node(pydot.Node(name=state, style = '', color = 'red', fontcolor = 'red'))

    def get_graph(self):
        """Return the source of the graph in string form"""
        return self.__fts.to_string()
