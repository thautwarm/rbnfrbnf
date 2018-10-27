import re
from rbnf.easy import Language, build_language, build_parser
from ast import fix_missing_locations
from astpretty import pprint
from rbnfrbnf import constructs
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

    return '\n'.join(_add_semi_comma(text))



result = parse(
    add_semi_comma("""
X := 'a'
A ::= ('b' | 'c' ('c' | 'a'))
Z ::= 'b'
recur F ::= 
    | Case1 name << A => f ?pre1 
    | Case2 ?pre2 B C

S ::= | S:  S a b c
      | F:  A b c
    
A ::= (?pre S a | B d)

S ::= 
    | S1 a 
    | S2 b

""")).result
fix_missing_locations(result)
pprint(result)
