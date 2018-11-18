from rbnfrbnf.core.tokenizer import Token, lexing
from rbnfrbnf.graph_runners.cfg.no_exc_handling import run_graph
from rbnfrbnf.bootstrap.cfg import parse
from rbnfrbnf.pgen import generate_parsing_graph_for_cfg
from pprint import pprint
from typing import List
grammar = """
Number  := R'\d+'
Numeric ::= Number | Number '.' Number | '-' Numeric
Add  ::= Atom ('+' Add) | Atom
Atom ::= Numeric | '(' Add ')'
"""

grammar_ast = parse(grammar).result

lexer_table, identified_nodes, all_nodes = generate_parsing_graph_for_cfg(
    grammar_ast)

tokens: List[Token] = list(
    lexing(
        filename='<test>', text='(1+1)', lexer_table=lexer_table, cast_map={}))

pprint(tokens)
pprint(run_graph(tokens, identified_nodes['Atom']))
