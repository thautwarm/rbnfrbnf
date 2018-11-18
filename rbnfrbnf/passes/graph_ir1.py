from singledispatch import singledispatch
from rbnfrbnf.core.constructs import *
from rbnfrbnf.core.syntax_graph import *
from rbnfrbnf.core.lexer_analysis import *
from .ir_constructs import *
from typing import List, Dict


class ContextForIR1:
    lexers: List[LiteralLexerDescriptor]
    token_typeids: Dict[str, int]

    def __init__(self):
        self.token_typeids = {}
        self.lexers = []


@singledispatch
def build_mid_graph(_, __):
    raise ValueError


@build_mid_graph.register(ParserC)
def _(p: ParserC, ctx: ContextForIR1):
    impl = build_mid_graph(p.impl, ctx)
    return Identified(p.name, tuple(impl))


@build_mid_graph.register(OrParserC)
def _(p: OrParserC, ctx: ContextForIR1):
    return sum((build_mid_graph(each, ctx) for each in p.brs), ())


@build_mid_graph.register(AndParserC)
def _(p: AndParserC, ctx: ContextForIR1):
    last = None
    for each in p.pats:
        cases = build_mid_graph(each, ctx)
        if last is not None:
            last = tuple(
                Chain(each_of_last, each_case)
                for each_case in cases
                for each_of_last in last)
        else:
            last = cases
    assert last is not None
    return last


@build_mid_graph.register(LiteralC)
def _(p: LiteralC, ctx: ContextForIR1):
    assert not p.prefix
    ctx.lexers.append(LiteralLexerDescriptor(0, p.value))
    return UnnamedTerminal(p.value),


@build_mid_graph.register(LexerC)
def _(p: LexerC, ctx: ContextForIR1):
    name = p.name
    descriptors = []
    typeid = ctx.token_typeids[name] = len(ctx.token_typeids) + 1
    append = descriptors.append
    for literal_c in p.lexers:
        value = literal_c.value
        descriptor_constructor = {
            'R': RegexLexerDescriptor,
            None: LiteralLexerDescriptor
        }[literal_c.prefix]
        append(descriptor_constructor(typeid, value))
    ctx.lexers.extend(descriptors)
    return


@build_mid_graph.register(RefC)
def _(p: RefC, ctx: ContextForIR1):
    if p.sym in ctx.token_typeids:
        return NamedTerminal(p.sym),
    return NamedNonTerminal(p.sym),


@build_mid_graph.register(ModuleC)
def _(p: ModuleC, ctx):
    return {
        each.name: each
        for each in [build_mid_graph(each, ctx) for each in p.seqs]
        if isinstance(each, Identified)
    }
