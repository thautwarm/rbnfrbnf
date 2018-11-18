import networkx
from matplotlib import pyplot as plt
from rbnfrbnf.core.syntax_graph import *
from typing import List


def attrs(node: Node):
    if isinstance(node, NamedTerminal):
        return id(node), 'lightgreen', repr(node), 300
    if isinstance(node, NonTerminalEnd):
        return id(node), 'pink', repr(node), 400
    if isinstance(node, UnnamedTerminal):
        return id(node), 'orange', repr(node), 300
    if isinstance(node, Identified):
        return id(node), 'lightblue', repr(node), 600
    if isinstance(node, SubRoutine):
        return id(node), 'teal', repr(node), 500


def plot_graph(nodes: List[Node]):
    g = networkx.DiGraph(format='weighted_adjacency_matrix')
    fig = plt.figure()
    plt.clf()
    numbers, colors, labels, sizes = zip(*map(attrs, nodes))
    g.add_nodes_from(numbers)
    labels = dict(zip(numbers, labels))
    for node in nodes:
        for parent in node.parents:
            g.add_edge(id(node), id(parent), weight=30)

    networkx.draw_networkx(
        g,
        labels=labels,
        node_size=sizes,
        node_color=colors,
        arrowsize=10,
        font_size=5)

    for each in fig.axes:
        each.axis('off')

    plt.savefig("plot.png", dpi=1000)
    plt.show()
