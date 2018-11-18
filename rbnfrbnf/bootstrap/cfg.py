from rbnf.easy import Language, build_language, build_parser
from rbnfrbnf.core import constructs
import re
import os

cfg = Language('cfg-rbnf')
test_line_start = re.compile('\S')


def add_semi_comma(text: str):

    def _add_semi_comma(text_formal: str):
        for each in text_formal.split('\n'):
            if test_line_start.match(each):
                yield ';'
            yield each
        yield ';'

    return '\n'.join(_add_semi_comma(text))


directory = os.path.split(__file__)[0]
with open(f'{directory}/context_free.rbnf') as f:
    source = f.read()

cfg.namespace = {**constructs.__dict__}
build_language(source, cfg, 'context_free.rbnf')
_parse = build_parser(cfg)


def parse(grammar):
    return _parse(add_semi_comma(grammar))
