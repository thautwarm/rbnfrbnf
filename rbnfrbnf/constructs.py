import ast
from rbnf.core.Tokenizer import Tokenizer
import typing as t


class Node(ast.expr):
    pass


class LexerC(Node):
    name: str
    lexers: t.Optional[t.List['LiteralC']]
    is_const: bool

    def __init__(self, name: Tokenizer, lexers, is_const):
        super().__init__()
        self.lineno = name.lineno
        self.col_offset = name.colno
        self.name = name.value
        self.lexers = lexers
        self.is_const = is_const

    _fields = ('name', 'lexers', 'is_const')


class ParserC(Node):
    name: str
    impl: Node

    def __init__(self, name: Tokenizer, impl):
        super().__init__()
        self.lineno = name.lineno
        self.col_offset = name.colno
        self.name = name.value
        self.impl = impl

    _fields = ('name', 'impl')


class OrParserC(Node):
    brs: t.List[Node]

    def __init__(self, brs: t.List[Node]):
        super().__init__()
        self.brs = brs

    _fields = ('brs', )


class CaseC(Node):
    name: str
    impl: Node

    def __init__(self, name, impl):
        super().__init__()
        self.lineno = name.lineno
        self.col_offset = name.colno
        self.name = name.value
        self.impl = impl

    _fields = ('name', 'impl')


class ADTParserC(Node):
    cases: t.List[CaseC]

    def __init__(self, cases):
        super().__init__()
        self.cases = cases

    _fields = ('cases', )


class AndParserC(Node):
    pats: t.List[Node]

    def __init__(self, pats: t.List[Node]):
        super().__init__()
        self.pats = pats

    _fields = ('pats', )


class RepC(Node):
    least: int
    most: int
    expr: Node

    def __init__(self, pat: t.List[Tokenizer], expr):
        super().__init__()
        if len(pat) is 1:
            self.least = int(pat[0].value)
            self.most = -1
        else:
            self.least, self.most = map(lambda _: int(_.value), pat)
        self.expr = expr

    _fields = ('least', 'most', 'expr')


class OptionalC(Node):

    expr: Node

    def __init__(self, expr: Node):
        super().__init__()
        self.expr = expr

    _fields = ('expr', )


class StarC(Node):

    expr: Node

    def __init__(self, expr: Node):
        super().__init__()
        self.expr = expr

    _fields = ('expr', )


class PlusC(Node):

    expr: Node

    def __init__(self, expr: Node):
        super().__init__()
        self.expr = expr

    _fields = ('expr', )


class RewriteC(Node):
    rewrite: str
    expr: Node

    def __init__(self, rewrite: Tokenizer, expr: Node):
        super().__init__()
        self.lineno = rewrite.lineno
        self.col_offset = rewrite.colno
        self.rewrite = rewrite.value
        self.expr = expr

    _fields = ('expr', 'rewrite')


class PredicateC(Node):
    predicate: str

    def __init__(self, predicate: Tokenizer):
        super().__init__()
        self.lineno = predicate.lineno
        self.col_offset = predicate.colno
        self.predicate = predicate.value

    _fields = ('predicate', )


class BindC(Node):
    bind_name: str
    expr: Node

    def __init__(self, predicate: Tokenizer, expr: Node):
        super().__init__()
        self.lineno = predicate.lineno
        self.col_offset = predicate.colno
        self.bind_name = predicate.value
        self.expr = expr

    _fields = ('expr', 'bind_name')


class PushC(Node):
    bind_name: str
    expr: Node

    def __init__(self, predicate: Tokenizer, expr: Node):
        super().__init__()
        self.lineno = predicate.lineno
        self.col_offset = predicate.colno
        self.bind_name = predicate.value
        self.expr = expr

    _fields = ('expr', 'bind_name')


class RefC(Node):

    sym: str

    def __init__(self, sym: Tokenizer):
        super().__init__()
        self.sym = sym.value
        self.lineno = sym.lineno
        self.col_offset = sym.colno

    _fields = ('sym', )


class LiteralC(Node):
    prefix: str
    value: str

    def __init__(self, lit: Tokenizer):
        super().__init__()
        self.lineno = lit.lineno
        self.col_offset = lit.colno
        value: str = lit.value
        if value.startswith('\''):
            self.value = eval(value)
            self.prefix = None
        else:
            self.value = eval(value[1:])
            self.prefix = value[0]

    _fields = ('prefix', 'value')


class ModuleC(Node):
    seqs: t.List[t.Union[ParserC, LexerC]]

    def __init__(self, seqs):
        super().__init__()
        self.seqs = seqs

    _fields = ('seqs', )
