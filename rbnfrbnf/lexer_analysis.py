from .utils import InternedString
import re
import abc
import typing as t

__all__ = [
    'Lexer', 'LexerDescriptor', 'RegexLexerDescriptor',
    'LiteralLexerDescriptor', 'lexer_reduce'
]
Lexer = t.Callable[[str, int], t.Optional[t.Tuple[int, str]]]


class LexerDescriptor(abc.ABC):
    typeid: int

    @abc.abstractmethod
    def to_lexer(self) -> Lexer:
        return self.to_lexer()


class RegexLexerDescriptor(LexerDescriptor):

    def __init__(self, typeid: int, regex_pat: str):
        self.typeid = typeid
        self.contents = regex_pat

    def to_lexer(self):
        match = re.compile(self.contents).match
        typeid = self.typeid
        box = InternedString

        def lex(string, pos):
            m = match(string, pos)
            if m:
                return box(m.group())

        return typeid, lex


class LiteralLexerDescriptor(LexerDescriptor):

    def __init__(self, typeid: int, *string_pats: str):
        assert string_pats
        self.typeid = typeid
        self.contents = string_pats

    def to_lexer(self):
        pats = self.contents
        typeid = self.typeid
        make_interned = InternedString
        if len(pats) is 1:
            pats = pats[0]

            def lex(string: str, pos):
                if string.startswith(pats, pos):
                    return make_interned(pats, typeid)
        else:

            def lex(string: str, pos):
                for pat in pats:
                    if string.startswith(pat, pos):
                        return make_interned(pat, typeid)

        return typeid, lex


def lexer_reduce(
        lexer_descriptors: t.List[LexerDescriptor]) -> t.List[LexerDescriptor]:

    def _chunk(stream: t.Iterable[LexerDescriptor]):
        grouped = []
        _append = grouped.append
        last = None
        for _e in stream:
            e = type(_e), _e.typeid
            if last is None:
                grouped = [_e]
                _append = grouped.append
            elif last == e:
                _append(_e)
            else:
                yield (last, grouped)
                grouped = [_e]
                _append = grouped.append
            last = e
        else:
            if last:
                yield (last, grouped)

    groups = list(_chunk(lexer_descriptors))

    ret = []
    for (lexer_type, typeid), descriptors in groups:

        if lexer_type is RegexLexerDescriptor:
            ret.extend(descriptors)
        else:
            assert lexer_type is LiteralLexerDescriptor
            descriptors: t.List[LiteralLexerDescriptor]
            contents = sum(tuple(each.contents for each in descriptors), ())

            ret.append(LiteralLexerDescriptor(typeid, *contents))

    return ret
