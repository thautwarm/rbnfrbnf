from rbnf.easy import Language, build_language, build_parser
from rbnfrbnf import constructs
from rbnfrbnf.graph_ir1 import build_mid_graph, ContextForIR1
from rbnfrbnf.graph_ir2 import ContextForIR2, terminate
from rbnfrbnf.graph_ir3 import prune, ContextForIR3, build_graph
from rbnfrbnf.lexer_analysis import lexer_reduce
from rbnfrbnf.tokenizer import lexing
from rbnfrbnf.run_graph import run_graph
from rbnfrbnf import syntax_graph
from rbnfrbnf import linked_lst
from tools.plot import plot_graph
import re

lang = Language('')

test_line_start = re.compile('\S')


def add_semi_comma(text: str):

    def _add_semi_comma(text_formal: str):
        for each in text_formal.split('\n'):
            if test_line_start.match(each):
                yield ';'
            yield each
        yield ';'

    return '\n'.join(_add_semi_comma(text))


with open('context_free.rbnf') as f:
    source = f.read()

lang.namespace = {**constructs.__dict__}
build_language(source, lang, 'context_free.rbnf')
parse = build_parser(lang)


def generate_parsing_graph(grammar):

    res = parse(add_semi_comma(grammar)).result
    ctx1 = ContextForIR1()
    res = build_mid_graph(res, ctx1)

    ctx2 = ContextForIR2(res)
    for each in res.values():
        terminate(each, ctx2)
    res = prune(ctx2.imp.values())
    ctx3 = ContextForIR3(ctx1.token_typeids, ctx2.imp.keys())
    for v in res:
        build_graph(v, ctx3)

    lexers = [each.to_lexer() for each in lexer_reduce(ctx1.lexers)]
    identified_nodes = ctx3.identified_nodes
    all_nodes = ctx3.all_nodes
    return lexers, identified_nodes, all_nodes


_grammar = """
Number  := R'\d+'
Numeric ::= '-' Number | '-' Number '.' Number

A ::= Numeric B | Numeric
B ::= Numeric A | Numeric
"""
lexers, ids, nodes = generate_parsing_graph(_grammar)
plot_graph(list(syntax_graph.get_connected_nodes(ids['A'])))
print(len(nodes))
# tokens = lexing('f', 'abc dd', lexers, {})
#
#
# print(
#     list(linked_lst.iterate(linked_lst.reverse(run_graph(tokens, ids['a'])))))
