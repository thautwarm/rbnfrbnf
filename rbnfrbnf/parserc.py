class Token:
    __slots__ = ('offset', 'lineno', 'colno', 'filename', 'type', 'value')

    def __init__(self, offset, lineno, colno, filename, type, value):
        self.offset = offset
        self.lineno = lineno
        self.colno = colno
        self.filename = filename
        self.type = type
        self.value = value

    def __iter__(self):
        yield self.offset
        yield self.lineno
        yield self.colno
        yield self.filename
        yield self.type
        yield self.value


class TokenView:
    __slots__ = ('source', 'offset')

    def __init__(self, offset, source):
        self.offset = offset
        self.source = source

    def split(self):
        if self.offset < len(self.source):
            offset = self.offset
            source = self.source
            yield source[offset]
            yield TokenView(offset + 1, source)
        else:
            yield


class ParsingError(Exception):
    pass


class Parser:
    __slots__ = ('parse_fn', )

    def __init__(self, parse_fn):
        self.parse_fn = parse_fn

    def __call__(self, view):
        return self.parse_fn(view)


def report_error_location(view):
    token = view.source[view.offset]
    raise ParsingError(
        f"parsing error at line {token.lineno}, column {token.colno}, file {token.filename}"
    )


def run_parse(parser, view):
    result = parser(view)
    if result:
        ret, view = result
        if view.offset == len(view.source):
            return ret

        report_error_location(view)

    report_error_location(view)


def literal(f):
    def parse(view):
        it = view.split()
        token = next(it)
        if token and f(token):
            return token, next(it)

    return parse


def both(pa, pb):
    def parse(view):
        it = pa(view)
        if not it:
            return it
        ret1, view = it
        it = pb(view)
        if not it:
            return it
        ret2, view = it
        return (ret1, ret2), view

    return parse


def all_of(p_seq):
    def parse(view):
        seq = []
        append = seq.append
        for p in p_seq:
            it = p(view)
            if not it:
                return
            e, view = it
            append(e)
        return seq

    return parse


def either(pa, pb):
    def parse(view):
        it = pa(view)
        if it:
            return it
        it = pb(view)
        if it:
            return it

    return parse


def one_of(p_seq):
    def parse(view):
        for p in p_seq:
            it = p(view)
            if not it:
                continue
            return it

    return parse


def rep(p, at_least, at_most):
    def parse(view):
        now = 0
        seq = []
        append = seq.append
        while now != at_most:
            it = p(view)
            if not it:
                break
            ret, view = it
            append(ret)
            now += 1

        if at_least <= now:
            return seq, view

    return parse


def any_token(view):
    it = view.split()
    ret = next(it)
    if ret:
        return ret, next(it)


def not_of(pa):
    def parse(view):
        if pa(view):
            return
        it = view.split()
        ret = next(it)
        if ret:
            return ret, next(it)

    return parse


def trans(parser, transform_func):
    def parse(token_view):
        it = parser(token_view)
        if not it:
            return it
        ret, token_view = it
        return transform_func(ret), token_view

    return parse


def pred(p, f):
    def parse(view):
        it = p(view)
        if not it:
            return it
        ret, view = it
        if f(ret):
            return ret, view

    return parse


def pgen(p):
    def parse(view):
        it = p(view)
        if not it:
            return it
        ret, view = it
        return ret(view)

    return parse
