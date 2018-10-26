from rbnf.easy import Language, build_language, build_parser
from ast import fix_missing_locations
from astpretty import pprint
with open('rbnf-bootstrap.rbnf') as f:
    code = f.read()

rbnf2 = Language('rbnf')
build_language(code, rbnf2, "rbnf-bootstrap.rbnf")

parse = build_parser(rbnf2)

result = parse("""
X := 'a' ;
A ::= 'b' | 'c' ('c' | 'a') ;
""").result

fix_missing_locations(result)
pprint(result)