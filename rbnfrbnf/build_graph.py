import ast
from rbnfrbnf import constructs
from rbnfrbnf.syntax_graph import SyntaxNode, NonTerminalNode, TerminalNode
from python_passes.utils import visitor


@visitor
class RBNFAstTransformer(ast.NodeVisitor):

    def __init__(self, pyfun_annotations=None):
        self.lexer_descriptors = []
        self.type_map = _AutoEnumDict()
        self.type_info = TypeInfoCollector()
        self.pyfun_annotations = pyfun_annotations or {}

    def analyzed(self) -> Analysis:
        enum_type: t.Type[IntEnum] = type('EnumType', (IntEnum, ),
                                          self.type_map)
        return Analysis(
            lexer_reduce(self.lexer_descriptors), enum_type,
            {**self.type_map})

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
        self.current_parser_case[_cat(self.current_parser_name,
                                      node.name)] = Struct(
                                          self.current_members)
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
        self.visit(node.expr)
        self.current_ty_spec = self.pyfun_annotations.get(
            node.rewrite) or Primitive('object')
        return node

    def visit_literal_c(self, node: constructs.LiteralC):
        self.current_ty_spec = Primitive('Token')
        return node
