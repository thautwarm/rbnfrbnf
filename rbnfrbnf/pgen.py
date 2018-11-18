from rbnfrbnf.core.constructs import Node as Ast
from rbnfrbnf.passes.graph_ir1 import build_mid_graph, ContextForIR1
from rbnfrbnf.passes.graph_ir2 import ContextForIR2, terminate
from rbnfrbnf.passes.graph_ir3 import prune, ContextForIR3, build_graph
from rbnfrbnf.core.lexer_analysis import lexer_reduce
from rbnfrbnf.core.syntax_graph import Identified, Node
from rbnfrbnf.core.lexer_analysis import Lexer
from typing import Dict, List, Tuple, Set


def generate_parsing_graph_for_cfg(
        grammar_ast: Ast
) -> Tuple[List[Lexer], Dict[str, Identified], Set[Node]]:
    grammar_ast = grammar_ast
    ctx1 = ContextForIR1()

    mid_graph = build_mid_graph(grammar_ast, ctx1)

    ctx2 = ContextForIR2(mid_graph)
    for each in mid_graph.values():
        terminate(each, ctx2)

    mid_graph2 = prune(ctx2.imp.values())
    ctx3 = ContextForIR3(ctx1.token_typeids, ctx2.imp.keys())
    for v in mid_graph2:
        build_graph(v, ctx3)

    lexer_table = [each.to_lexer() for each in lexer_reduce(ctx1.lexers)]
    identified_nodes = ctx3.identified_nodes
    all_nodes = ctx3.all_nodes
    return lexer_table, identified_nodes, all_nodes
