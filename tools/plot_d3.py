import networkx
from matplotlib import pyplot as plt
from rbnfrbnf.syntax_graph import *
from rbnfrbnf.utils import IdAllocator
from tools.data_schema import *
from typing import List


def plot_graph(nodes: List[Node]):
    id_allocator = IdAllocator()
    for each in nodes:
        id_allocator.add(each)
    id = id_allocator.get_identifier

    def attrs(node: Node):
        if isinstance(node, NamedTerminal):
            return id(node), 'orange', repr(node), 6
        if isinstance(node, NonTerminalEnd):
            return id(node), 'pink', repr(node), 6
        if isinstance(node, UnnamedTerminal):
            return id(node), 'blue', repr(node), 5
        if isinstance(node, Identified):
            return id(node), 'red', repr(node), 8
        if isinstance(node, SubRoutine):
            return id(node), 'teal', repr(node), 7
        if isinstance(node, TerminalEnd):
            return id(node), 'yellow', repr(node), 4
        if isinstance(node, Dispatcher):
            return id(node), 'green', repr(node), 6

    json_nodes = list(
        map(lambda number, color, label, size: make_node(id=number, text=label, title=label, color=color, size=size),
            *zip(*map(attrs, nodes))))

    json_links = []
    for node in nodes:
        for parent in node.parents:
            json_links.append(
                make_link(start=id(node), end=id(parent), value=3))

    return {
        'width': 1200,
        'height': 1000,
        'data': {
            'links': json_links,
            'nodes': json_nodes
        }
    }
