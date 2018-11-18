from Redy.Magic.Classic import record
from typing import Tuple


class Node:

    def __iter__(self):
        raise TypeError


class Terminal(Node):
    pass


class NonTerminal:
    pass


@record
class Identified(Node):
    name: str
    children: tuple

    def __repr__(self):
        return '%s = %s' % (self.name, repr(self.children))


@record
class UnnamedTerminal(Terminal):
    value: str

    def __repr__(self):
        return repr(self.value)


@record
class NamedTerminal(Terminal):
    name: str

    def __repr__(self):
        return self.name


@record
class NamedNonTerminal(NonTerminal):
    name: str

    def __repr__(self):
        return self.name


@record
class Chain(NonTerminal):
    l: Node
    r: Node

    def leaf(self):
        r = self.r

        while isinstance(r, Chain):
            r = r.leaf()
        return r

    def __repr__(self):
        return repr(self.l) + '->' + repr(self.r)


@record
class NonTerminalEnd(Node):
    name: str

    def __repr__(self):
        return '$%s' % self.name


@record
class TerminalEnd(Node):

    def __repr__(self):
        return r'$\epsilon$'


@record
class MultiParents(Node):
    root: Node
    targets: Tuple[Node, ...]

    def __repr__(self):
        a = '|'.join(map(repr, self.targets))
        b = repr(self.root)
        return '%s -> (%s)' % (b, a)


@record
class LeftRecur(Node):
    pass
