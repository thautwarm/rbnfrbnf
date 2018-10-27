import typing as t

from rbnfrbnf.parserc import Token
from rbnfrbnf.state import State

T = t.TypeVar('T')
G = t.TypeVar('G')


class SyntaxNode:
    pass


class TerminalNode(SyntaxNode):
    predicate: t.Callable[[Token], bool]
    parents: t.List[SyntaxNode]


class NonTerminalNode(SyntaxNode, t.Generic[T]):
    rewrite: t.Callable[[State], T]
    parents: t.List[SyntaxNode]

