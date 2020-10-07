import pydot
import os

class Graph():
    __slots__ = '__graph'

    def __init__(self, data):
        self.__graph = pydot.graph_from_dot_data(data)[0]
        self.__graph.obj_dict['attributes']['rankdir'] = 'TB'

    @classmethod
    def from_file(self, filename):
        with open(filename, 'r') as source:
            data = source.read()
            return self(data)

    def draw_graph(self, target):
        if(len(self.__graph.get_edges()) <= 300):
            svg = self.__graph.create_svg()
            if target:
                with open(target,'wb') as out:
                    out.write(svg)
                    return True
        return False

    def __draw_graph(self, graph, target):
        if(len(graph.get_edges()) <= 300):
            svg = graph.create_svg()
            if target:
                with open(target,'wb') as out:
                    out.write(svg)
                    return True
        return False

    def draw_mts(self, target=None):
        tmp = pydot.graph_from_dot_data(self.__graph.to_string())[0]
        for edge in tmp.get_edges():
            attr = edge.obj_dict['attributes']
            if (attr['label'][1:-1].split('|')[-1].strip() != 'True'):
                attr['style'] = "dashed"
            attr['label'] = attr['label'][1:-1].split('|')[0] 
            self.__draw_graph(tmp, target)
        return tmp.to_string()

    def get_graph_number(self):
        node = list()
        for edge in self.__graph.get_edges():
            if edge.get_source() not in node:
                node.append(edge.get_source())
            if edge.get_destination() not in node:
                node.append(edge.get_destination())
        return len(self.__graph.get_edges()), len(node)

    def get_graph(self):
        return self.__graph.to_string()
