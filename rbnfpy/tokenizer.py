from warnings import warn


class InternedString:
    STRINGS = {}
    i: int
    s: str

    @classmethod
    def make(cls, s: str):
        pool = cls.STRINGS
        i = pool.get(s, None)
        if i is None:
            i = pool[s] = len(s)
        return InternedString(s, i)

    def __init__(self, s: str, i=0):
        self.s = s
        self.i = i

    def as_interned(self):
        return self.make(self.s)

    def __repr__(self):
        return 'InternedStr({{!r}}, is_interned={{}})'.format(
            self.s, self.i == 0)

    def __str__(self):
        return 'InternedStr({{!r}}, is_interned={{}})'.format(
            self.s, self.i == 0)


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
    tokens = []
    append = tokens.append
    make_interned = InternedString.make

    while True:
        if text_length <= pos:
            break

        for typeid, case in lexer_table:
            pat = case(text, pos)

            if pat is None:
                continue

            casted_typeid = cast_map.get(pat)
            if casted_typeid is None:
                interned_string = InternedString(pat)
                append(
                    Token(pos, lineno, colno, filename, typeid,
                          interned_string))
            else:
                interned_string = make_interned(pat)
                append(
                    Token(pos, lineno, colno, filename, casted_typeid,
                          interned_string))
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
            append(Token(pos, lineno, colno, filename, 0, interned_string))
            if ch == "\n":
                lineno += 1
                colno = 0
            pos += 1

    return tokens
