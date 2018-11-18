from warnings import warn
from .utils import InternedString


class Token:
    offset: int
    lineno: int
    colno: int
    filename: str
    type: int
    value: InternedString
    _repr: str
    __slots__ = ('offset', 'lineno', 'colno', 'filename', 'type', 'value',
                 '_repr')

    def __init__(self, offset, lineno, colno, filename, type, value):
        self.offset = offset
        self.lineno = lineno
        self.colno = colno
        self.filename = filename
        self.type = type
        self.value = value
        self._repr = None

    def __eq__(self, other: 'Token'):
        if not isinstance(other, Token):
            return False

        return (self.offset == other.offset and self.filename == other.filename
                and self.type == other.type and self.value == other.value
                and self.colno == other.colno and self.lineno == other.lineno)

    def __hash__(self):
        return (
            self.offset ^ self.lineno ^ self.colno + 2333 + self.type) ^ hash(
                self.filename) ^ hash(self.value.i) ^ hash(self.value.s)

    def __repr__(self):
        if self._repr is None:
            self._repr = "Token(offset=%d, lineno=%d, colno=%d, filename=%s, type=%d, value=%s)" % (
                self.offset, self.lineno, self.colno, self.filename, self.type,
                self.value.s)
        return self._repr


def lexing(filename: str, text: str, lexer_table: list, cast_map: dict):
    text_length = len(text)
    colno = 0
    lineno = 0
    pos = 0
    newline = '\n'

    while True:
        if text_length <= pos:
            break

        for typeid, case in lexer_table:
            interned_string: InternedString = case(text, pos)

            if interned_string is None:
                continue
            pat = interned_string.s
            casted_typeid = cast_map.get(pat)
            if casted_typeid is None:
                yield Token(pos, lineno, colno, filename, typeid,
                            interned_string)
            else:

                yield Token(pos, lineno, colno, filename, casted_typeid,
                            interned_string.as_interned())
            n = len(pat)
            line_inc = pat.count(newline)
            if line_inc:
                latest_newline_idx = pat.rindex(newline)
                colno = n - latest_newline_idx
                lineno += line_inc
            else:
                colno += n
            pos += n
            break

        else:
            warn(f"No handler for character `{text[pos].__repr__()}`.")
            ch = text[pos]
            interned_string = InternedString(ch)
            yield Token(pos, lineno, colno, filename, 0, interned_string)
            if ch == "\n":
                lineno += 1
                colno = 0
            pos += 1
