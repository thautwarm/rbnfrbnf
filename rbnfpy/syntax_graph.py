import typing as t


class Node:
    parents: t.List['Node']
    children: t.List['Node']

    def as_parent_of(self, node: 'Node'):
        if self not in node.parents:
            node.parents.append(self)
            self.children.append(node)

    def as_child_of(self, node: 'Node'):
        node.as_parent_of(self)


class Identified(Node):

    def __init__(self, name):
        self.name = name
        self.parents = []
        self.children = []
        self.starts = []

    def __repr__(self):
        return self.name


class SubRoutine(Node):

    def __init__(self, root: Identified):
        self.root = root
        self.parents = []
        self.children = []

    def __repr__(self):
        return repr(self.root)


class UnnamedTerminal(Node):

    def __init__(self, value, name=None):
        self.name = name or '%s' % repr(value.s)
        self.value = value
        self.parents = []
        self.children = []

    def __repr__(self):
        return self.name


class NamedTerminal(Node):

    def __init__(self, typeid, name=None):
        self.typeid = typeid
        self.name = name or 'nameOf(%d)' % typeid
        self.parents = []
        self.children = []

    def __repr__(self):
        return self.name


class NonTerminalEnd(Node):

    def __init__(self, name):
        self.name = name
        self.parents = []
        self.children = []

    def __repr__(self):
        return 'endOf(%s)' % self.name


class TerminalEnd(Node):

    def __init__(self):
        self.parents = []
        self.children = []

    def __repr__(self):
        return r'$\epsilon$'


def get_leaves(*nodes) -> t.List[Node]:

    def get_it(node: Node, recur=None):
        recur = recur or set()
        if node in recur:
            return
        children = node.children
        if not children:
            yield node
        else:
            for each in children:
                yield from get_it(each, {*recur, node})

    def _():
        c = set()
        for _ in map(get_it, nodes):
            for __ in _:
                if __ not in c:
                    c.add(__)
                    yield __

    return list(_())


def get_roots(*nodes) -> t.List[Node]:

    def get_it(node: Node, recur=None):
        recur = recur or set()
        if node in recur:
            return
        parents = node.parents
        if not parents:
            yield node
        else:
            for each in parents:
                yield from get_it(each, {*recur, node})

    def _():
        c = set()
        for _ in map(get_it, nodes):
            for __ in _:
                if __ not in c:
                    c.add(__)
                    yield __

    return list(_())


def get_connected_nodes(*nodes) -> t.Set[Node]:
    recur = {*()}

    def get_it(node: Node):
        if node in recur:
            return
        recur.add(node)
        for each in node.parents:
            get_it(each)
        for each in node.children:
            get_it(each)

    for node in nodes:
        get_it(node)

    return recur


# A = NonTerminalEnd('A')
# B = NonTerminalEnd("B")
# C = NonTerminalEnd('C')
# D = NonTerminalEnd('D')
# A.as_parent_of(B)
# B.as_parent_of(C)
# B.as_parent_of(D)
#
# print(get_leaves(A))
