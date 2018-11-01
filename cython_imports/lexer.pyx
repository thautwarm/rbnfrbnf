# distutils: language = c++
from libcpp.vector cimport vector
from cython.operator cimport dereference, preincrement
from libcpp.unordered_map cimport unordered_map
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t, int8_t, int64_t, int32_t
from libc.stdlib cimport malloc, free
cimport cython
from libcpp.string cimport string
import io
from warnings import warn

cdef unordered_map[string, uint64_t] interned_pool
ctypedef unsigned long size_t

cdef _InternedString make_interned(string s):
    cdef unordered_map[string, uint64_t].iterator it = interned_pool.find(s)
    cdef uint64_t i = 0
    cdef _InternedString ret

    if it == interned_pool.end():
        i = interned_pool.size() + 1
        interned_pool[s] = i
    else:
        i = dereference(it).second

    ret.i = i
    ret.s = s
    return ret

cdef struct _InternedString:
    uint64_t i
    string   s

cdef class InternedString:
    cdef _InternedString s

    def __init__(self, string s):
        self.s = _InternedString(0, s)

    cdef access(self, _InternedString s):
        self.s = s

    def __repr__(self):
        return 'InternedStr({{!r}}, is_interned={{}})'.format(self.s.s, self.s.i == 0)

    def __str__(self):
        return 'InternedStr({{!r}}, is_interned={{}})'.format(self.s.s, self.s.i == 0)

cdef class Token:
    cdef public uint64_t offset
    cdef public uint64_t lineno
    cdef public uint64_t colno
    cdef public str    filename
    cdef public uint16_t type
    cdef public _InternedString value
    cdef object _repr

    def __init__(self, int offset, int lineno, int colno, str filename, int type, InternedString value):
        self.offset = offset
        self.lineno = lineno
        self.colno = colno
        self.filename = filename
        self.type = type
        self.value = value.s
        self._repr = None

    def __hash__(self):
        return (self.offset ^ self.lineno ^ self.colno + 2333 + self.type) ^ hash(self.filename) ^ hash(
                self.value.i) ^ hash(self.value.s)

    def __repr__(self):
        if self._repr is None:
            self._repr = "Token(offset=%d, lineno=%d, colno=%d, filename=%s, type=%d, value=%s)" % (
                self.offset, self.lineno, self.colno, self.filename, self.type, self.value.s)
        return self._repr

cdef lexing(string filename, str text, list lexer_table, unordered_map[string, uint16_t] cast_map):
    cdef uint64_t text_length = len(text)
    cdef uint64_t colno = 0
    cdef uint64_t lineno = 0
    cdef uint64_t pos = 0
    cdef uint64_t n = 0
    cdef string pat_s
    cdef string ch
    cdef _InternedString interned_string
    cdef unordered_map[string, uint16_t].iterator end_of_cast_map = cast_map.end()
    cdef unordered_map[string, uint16_t].iterator found_result
    cdef InternedString acc = InternedString('')

    newline = '\n'
    tokens = []
    append = tokens.append

    while True:
        if text_length <= pos:
            break

        for typeid, case in lexer_table:
            pat = case(text, pos)

            if not pat:
                continue

            pat_s = pat
            found_result = cast_map.find(pat_s)
            if end_of_cast_map == found_result:
                interned_string = _InternedString(0, pat_s)
                acc.access(interned_string)
                append(Token(pos, lineno, colno, filename, typeid, acc))

            else:
                interned_string = make_interned(pat_s)
                typeid = dereference(found_result).second
                append(Token(pos, lineno, colno, filename, typeid, acc))
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
            interned_string = _InternedString(0, ch)
            acc.access(interned_string)
            append(Token(pos, lineno, colno, filename, 0, acc))
            if ch == "\n":
                lineno += 1
                colno = 0
            pos += 1
