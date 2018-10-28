import ast
import typing as t
from enum import IntEnum
from rbnfrbnf import constructs
from python_passes.utils import visitor
from .lexer_analysis import *
from .type_analysis import *
K = t.TypeVar('T')
V = t.TypeVar('G')


def _cat(a, b):
    return f"{a}_{b}"


class Analysis(t.NamedTuple):
    lexer_table: t.List[Lexer]
    type_info: TypeInfoCollector
    type_map: t.Dict[str, int]
    py_funcs: t.Dict[str, 'function']
    enum_type: t.Type[IntEnum]


class _AutoEnumDict(dict, t.Generic[K]):

    def __missing__(self, key: K):
        value = len(self)
        self[key] = value
        return value


@visitor
class Analyzer(ast.NodeTransformer):

    lexer_descriptors: t.List[LexerDescriptor]
    type_map: _AutoEnumDict[str]
    type_info: TypeInfoCollector
    py_funcs: t.Dict[str, 'function']
    # temporary state

    current_ty_spec: TypeSpec
    current_parser_case: t.Dict[str, TypeSpec]
    current_members: t.Dict[str, TypeSpec]
    current_parser_name: str

    def __init__(self, py_funcs: t.Dict[str, 'function'] = None):
        self.lexer_descriptors = []
        self.type_map = _AutoEnumDict()
        self.type_info = TypeInfoCollector()
        self.py_funcs = py_funcs or {}

    def analyzed(self) -> Analysis:
        enum_type: t.Type[IntEnum] = type('EnumType', (IntEnum, ),
                                          self.type_map)
        return Analysis(
            lexer_reduce(self.lexer_descriptors), self.type_info,
            {**self.type_map}, self.py_funcs, enum_type)

    def typeid_of(self, typename: str):
        return self.type_map[typename]

    def visit_lexer_c(self, node: constructs.LexerC):
        self.type_info.register_type(node.name, Primitive('Token'))
        typeid = self.type_map[node.name]

        append = self.lexer_descriptors.append
        for literal_c in node.lexers:
            value = literal_c.value
            descriptor_constructor = {
                'R': RegexLexerDescriptor,
                None: LiteralLexerDescriptor
            }[literal_c.prefix]
            append(descriptor_constructor(typeid, value))
        return []

    def visit_parser_c(self, node: constructs.ParserC):
        self.current_members = {}
        name = self.current_parser_name = node.name
        self.visit(node.impl)
        self.type_info.register_type(name, self.current_ty_spec)
        return node

    def visit_a_d_t_parser_c(self, node: constructs.ADTParserC):
        self.current_parser_case = {}
        self.generic_visit(node)
        adt = ADT(self.current_parser_case)
        self.current_ty_spec = adt
        return node

    def visit_case_c(self, node: constructs.CaseC):
        self.visit(node.impl)
        name = _cat(self.current_parser_name, node.name)
        self.current_parser_case[name] = Struct(name, self.current_members)
        return node

    def visit_or_parser_c(self, node: constructs.OrParserC):
        unions = []
        union = Union(unions)
        for each in node.brs:
            self.visit(each)
            unions.append(self.current_ty_spec)
        self.current_ty_spec = union
        return node

    def visit_and_parser_c(self, node: constructs.AndParserC):
        gathers = []
        gather = Tuple(gathers)
        for each in node.pats:
            if isinstance(each, constructs.PredicateC):
                continue
            self.visit(each)
            gathers.append(self.current_ty_spec)
        if len(gathers) is 1:
            gather = gathers[0]
        self.current_ty_spec = gather
        return node

    def visit_bind_c(self, node: constructs.BindC):
        self.visit(node.expr)
        self.current_members[node.bind_name] = self.current_ty_spec
        return node

    def visit_push_c(self, node: constructs.PushC):
        self.visit(node.expr)
        self.current_members[node.bind_name] = List(self.current_ty_spec)
        return node

    def visit_plus_c(self, node: constructs.PlusC):
        self.visit(node.expr)
        self.current_ty_spec = List(self.current_ty_spec)
        return node

    def visit_star_c(self, node: constructs.StarC):
        self.visit(node.expr)
        self.current_ty_spec = Optional(List(self.current_ty_spec))

    def visit_optional_c(self, node: constructs.OptionalC):
        self.visit(node)
        self.current_ty_spec = Optional(self.current_ty_spec)
        return node

    def visit_rep_c(self, node: constructs.RepC):
        self.visit(node.expr)
        container = List
        if node.least is 0:

            def container(it):
                return Optional(container(it))

        self.current_ty_spec = container(self.current_ty_spec)
        return node

    def visit_ref_c(self, node: constructs.RefC):
        self.current_ty_spec = ForwardRef(node.sym)
        return node

    def visit_rewrite_c(self, node: constructs.RewriteC):

        def _get_return_ty(fn: 'function'):
            if fn:
                return fn.__annotations__.get('return').__name__

        self.visit(node.expr)
        self.current_ty_spec = _get_return_ty(self.py_funcs.get(
            node.rewrite)) or Primitive('object')
        return node

    def visit_literal_c(self, node: constructs.LiteralC):
        self.current_ty_spec = Primitive('Token')
        return node
