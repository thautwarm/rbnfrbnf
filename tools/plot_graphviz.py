from rbnfrbnf.syntax_graph import *
from rbnfrbnf.utils import IdAllocator
from typing import List
from graphviz import Digraph


def plot_graph(nodes: List[Node]):
    id_allocator = IdAllocator()
    for each in nodes:
        id_allocator.add(each)
    id = id_allocator.get_identifier

    def attrs(node: Node):
        if isinstance(node, NamedTerminal):
            return id(node), None, repr(node), 4
        if isinstance(node, NonTerminalEnd):
            return id(node), 'ellipse', repr(node), 4
        if isinstance(node, UnnamedTerminal):
            return id(node), None, repr(node), 3
        if isinstance(node, Identified):
            return id(node), 'circle', repr(node), 6
        if isinstance(node, SubRoutine):
            return id(node), 'doublecircle', repr(node), 5
        if isinstance(node, TerminalEnd):
            return id(node), 'ellipse', repr(node), 3

    g = Digraph()
    for number, shape, label, _ in map(attrs, nodes):
        attrs = {'name': str(number), 'label': label}
        if shape:
            attrs['shape'] = shape
        g.node(**attrs)

    for node in nodes:
        for parent in node.parents:
            g.edge(str(id(node)), str(id(parent)))

    g.view()
