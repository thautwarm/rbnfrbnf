import ast
import typing as t
from enum import IntEnum
from rbnfrbnf import constructs
from python_passes.utils import visitor
from cython_interface2.analysis import TypeAnalysis
from cython_interface2.codegen import mk_types
from cython_interface2.types import *
from .lexer_analysis import *
import operator
from toolz import compose, curry
K = t.TypeVar('T')
V = t.TypeVar('G')


def _cat(a, b):
    return f"{a}_{b}"


class Analysis(t.NamedTuple):
    lexer_table: t.List[Lexer]
    type_collector: TypeAnalysis
    type_map: t.Dict[str, int]
    py_funcs: t.Dict[str, 'function']


class _AutoEnumDict(dict, t.Generic[K]):

    def __missing__(self, key: K):
        value = len(self)
        self[key] = value
        return value


@visitor
class Analyzer(ast.NodeTransformer):

    lexer_descriptors: t.List[LexerDescriptor]
    type_map: _AutoEnumDict[str]
    type_collector: TypeAnalysis
    py_funcs: t.Dict[str, 'function']
    # temporary state

    current_ty_spec: TypeSpec
    current_parser_case: t.Dict[str, TypeSpec]
    current_members: t.Dict[str, TypeSpec]
    current_parser_name: str

    def __init__(self, py_funcs: t.Dict[str, 'function'] = None):
        self.lexer_descriptors = []
        self.type_map = _AutoEnumDict()
        self.type_collector = TypeAnalysis()
        self.py_funcs = py_funcs or {}

    def analyzed(self) -> Analysis:
        return Analysis(
            lexer_reduce(self.lexer_descriptors), self.type_collector,
            {**self.type_map}, self.py_funcs)

    def typeid_of(self, typename: str):
        return self.type_map[typename]

    def visit_lexer_c(self, node: constructs.LexerC):
        self.type_collector.define(node.name, Primitive('Token'))
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
        self.type_collector.define(name, self.current_ty_spec)
        return node

    def visit_a_d_t_parser_c(self, node: constructs.ADTParserC):
        self.current_parser_case = {}
        self.generic_visit(node)
        adt = TaggedUnion(ImmutableMap.from_dict(self.current_parser_case))
        self.current_ty_spec = adt
        return node

    def visit_case_c(self, node: constructs.CaseC):
        self.current_members = {}
        self.visit(node.impl)
        case_name = node.name
        self.current_parser_case[case_name] = Struct(
            ImmutableMap.from_dict(self.current_members))
        return node

    def visit_or_parser_c(self, node: constructs.OrParserC):
        unions = []
        for each in node.brs:
            self.visit(each)
            unions.append(self.current_ty_spec)

        if len(set(unions)) is 1:
            union = unions[0]
        else:
            union = Primitive('object')

        self.current_ty_spec = union
        return node

    def visit_and_parser_c(self, node: constructs.AndParserC):
        gathers = []
        for each in node.pats:
            if isinstance(each, constructs.PredicateC):
                continue
            self.visit(each)
            gathers.append(self.current_ty_spec)
        if len(gathers) is 1:
            gather = gathers[0]
        else:
            gather = Tuple(SizedList.from_list(gathers))
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
        self.current_ty_spec = List(self.current_ty_spec)

    def visit_optional_c(self, node: constructs.OptionalC):
        self.visit(node)
        ty_spec = self.current_ty_spec
        ty_spec = TaggedUnion(
            ImmutableMap.from_dict({
                'None': Primitive('object'),
                'Some': ty_spec
            }))

        self.current_ty_spec = ty_spec
        return node

    def visit_rep_c(self, node: constructs.RepC):
        self.visit(node.expr)
        self.current_ty_spec = List(self.current_ty_spec)
        return node

    def visit_ref_c(self, node: constructs.RefC):
        self.current_ty_spec = ForwardRef(node.sym)
        return node

    def visit_rewrite_c(self, node: constructs.RewriteC):

        def _get_return_ty(fn: 'function'):
            if fn:
                return Primitive(fn.__annotations__.get('return').__name__)

        self.visit(node.expr)
        self.current_ty_spec = _get_return_ty(self.py_funcs.get(
            node.rewrite)) or Primitive('object')
        return node

    def visit_literal_c(self, node: constructs.LiteralC):
        self.current_ty_spec = Primitive('Token')
        return node
