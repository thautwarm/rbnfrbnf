import re
import astpretty
import pprint
from rbnf.easy import Language, build_language, build_parser
from ast import fix_missing_locations
from rbnfrbnf import constructs
from rbnfrbnf.grammar_analysis.grammar_analyzer import Analyzer, mk_types
from cython_interface2.types import Struct, ImmutableMap

with open('rbnf-bootstrap.rbnf') as f:
    code = f.read()

rbnf2 = Language('rbnf')
rbnf2.namespace.update(constructs.__dict__)
build_language(code, rbnf2, "rbnf-bootstrap.rbnf")
test_line_start = re.compile('\S')
parse = build_parser(rbnf2)


def add_semi_comma(text: str):

    def _add_semi_comma(text_formal: str):
        for each in text_formal.split('\n'):
            if test_line_start.match(each):
                yield ';'
            yield each
        yield ';'

    return '\n'.join(_add_semi_comma(text))


result = parse(
    add_semi_comma(r"""
Num   := R'\d+'
X     := 'a'
Z     ::= 'b'
Id    := R'[a-zA-Z_]{1}[a-zA-Z_0-9]*'
Space := '\s+'

F ::= 
    | Case1 : name << A => f ?pre1 
    | Case2 : ?pre2 B C

D ::= | S:  S a b c
      | F:  A b c
    
A ::= (?pre S | B d)

S ::= 
    | S1: a
    | S2: b

""")).result
fix_missing_locations(result)
# astpretty.pprint(result)
analyzer = Analyzer()
analyzer.visit(result)
analyzed = analyzer.analyzed()
analyzed.type_collector.resolve()

S = analyzed.type_collector.load_type('S')
# print(analyzed.type_collector.mk_types().decode())
pprint.pprint(list(analyzed.type_collector.mod.__dict__.keys()))

S1 = analyzed.type_collector.load_constructor('S', 'S1')
empty_struct_type = analyzed.type_collector.load_type(Struct(ImmutableMap(())))
print(isinstance(S1(empty_struct_type()), S))
