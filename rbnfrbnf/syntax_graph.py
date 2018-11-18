import typing as t


class Node:
    children: t.List['Node']

    @property
    def parents(self) -> t.List['Node']:
        raise NotImplemented

    def as_child_of(self, node):
        raise NotImplemented


globals()['Node'] = object


class Single(Node):
    parent: t.Optional['Node']

    @property
    def parents(self):
        parent = self.parent
        if self.parent:
            return parent,
        return ()

    def as_child_of(self, node: Node):
        parent = self.parent
        if parent:
            if not isinstance(parent, Dispatcher):
                self.parent = new_node = Dispatcher()
                parent.children.remove(self)
                new_node.children.append(self)
                new_node.as_child_of(parent)
                new_node.as_child_of(node)

            else:
                parent.as_child_of(node)

        else:
            node.children.append(self)
            self.parent = node


class Multi(Node):
    parents: t.List['Node']

    def as_child_of(self, node: Node):
        node.children.append(self)
        self.parents.append(node)


class Identified(Single):

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []
        self.starts = []

    def __repr__(self):
        return self.name


class SubRoutine(Single):

    def __init__(self, root: Identified):
        self.root = root
        self.parent = None
        self.children = []

    def __repr__(self):
        return repr(self.root)


class UnnamedTerminal(Single):

    def __init__(self, value, name=None):
        self.name = name or '%s' % repr(value.s)
        self.value = value
        self.parent = None
        self.children = []

    def __repr__(self):
        return self.name


class NamedTerminal(Single):

    def __init__(self, typeid, name=None):
        self.typeid = typeid
        self.name = name or 'nameOf(%d)' % typeid
        self.parent = None
        self.children = []

    def __repr__(self):
        return self.name


class NonTerminalEnd(Single):

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []

    def __repr__(self):
        return 'endOf(%s)' % self.name


class TerminalEnd(Single):

    def __init__(self):
        self.parent = None
        self.children = []

    def __repr__(self):
        return r'$\epsilon$'


class Dispatcher(Multi):
    parents: t.List[Node]
    children: t.List[Node]

    def __init__(self):
        self.parents = []
        self.children = []

    def __repr__(self):
        return 'dispatcher'


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
            recur = {*recur, node}
            for each in parents:
                yield from get_it(each, recur)

    # TODO: rationally naming
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

    def get_it(arg: Node):
        if arg in recur:
            return
        recur.add(arg)
        for each in arg.parents:
            get_it(each)
        for each in arg.children:
            get_it(each)

    for node in nodes:
        get_it(node)

    return recur
