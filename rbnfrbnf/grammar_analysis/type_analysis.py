import typing as t

__all__ = [
    'TypeInfoCollector', 'TypeSpec', 'Tuple', 'ADT', 'ForwardRef', 'Optional',
    'List', 'Union', 'Struct', 'Primitive'
]


class TypeSpec:
    pass


class ForwardRef(TypeSpec, t.NamedTuple):
    name: str


class Primitive(TypeSpec, t.NamedTuple):
    typename: str


class Optional(TypeSpec, t.NamedTuple):
    typ: TypeSpec


class Union(TypeSpec, t.NamedTuple):
    args: t.List[TypeSpec]


class List(TypeSpec, t.NamedTuple):
    elem: TypeSpec


class Struct(TypeSpec, t.NamedTuple):
    name: str
    fields: t.Dict[str, TypeSpec]


class Tuple(TypeSpec, t.NamedTuple):
    elem: t.List[TypeSpec]


_TypeSpec = (ForwardRef, Primitive, Optional, Union, List, Struct, Tuple)


class ADT(TypeSpec, t.NamedTuple):
    cases: t.Dict[str, TypeSpec]


class TypeInfoCollector:
    type_tables: t.Dict[str, TypeSpec]

    def __init__(self):
        self.type_tables = {}

    def remove(self, typename):
        del self.type_tables[typename]

    def register_type(self, name, spec):
        self.type_tables[name] = spec

    def mk_type(self, cy=True):
        pass


class _TypeSpecVisitor:
    dispatcher: t.Dict[type, 'function']

    def visit(self, node: TypeSpec):
        return self.dispatcher.get(type(node), self.generic_visit)(node)

    def generic_visit(self, node: tuple):
        if isinstance(node, _TypeSpec):
            visit = self.visit
            return node.__class__(*(visit(each) for each in node))
        return node


def dispatch(dispatcher):

    def dispatch_for(ty: type):

        def register(f):
            dispatcher[ty] = f
            return f

        return register

    return dispatch_for


CythonPreDef = """
from libc.stdint cimport uint64_t
cdef class Token:
    cdef public uint64_t offset
    cdef public uint64_t lineno
    cdef public uint64_t colno
    cdef public char*    filename
    cdef public uint16_t type
    cdef public char*    value
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
"""


class CythonTypeCodegen(_TypeSpecVisitor):
    dispatcher = {}
    _dispatch = dispatch(dispatcher)

    def __init__(self, ios=print):
        self.ios = ios
        self.tmp_types = []
        ios(CythonPreDef)

    def _def_fused(self, ty_name, *brs: Struct):
        ios = self.ios
        ios('cdef fused ')
        ios(ty_name)
        ios(':')
        ios('\n')
        for each in brs:
            ios('    ')
            ios(each.name)
            ios('\n')
        ios('\n')

    def _def_struct(self, ty_name, **fields):
        ios = self.ios
        ios('cdef class ')
        ios(ty_name)
        ios(':')
        ios('\n')
        for field_name, field_ty in fields.items():
            ios('    ')
            ios('cdef public ')
            self.visit(field_ty)
            ios(' ')
            ios(field_name)
            ios('\n')

        ios('\n')

        ios('    ')
        ios('def __init__(self')
        for field_name, field_ty in fields.items():
            ios(', ')
            self.visit(field_ty)
            ios(' ')
            ios(field_name)
        ios('):\n')
        for each in fields:
            ios('    ')
            ios('    ')
            ios('self.')
            ios(each)
            ios(' = ')
            ios(each)
            ios('\n')

        ios('\n')

    @_dispatch(Struct)
    def visit_struct(self, node: Struct):
        self._def_struct(node.name, **node.fields)

    @_dispatch(ADT)
    def visit_adt(self, node: ADT):
        base_name, brs = zip(*[each.split('.') for each in node.cases])
        base_name = base_name[0]
        values = [*node.cases.values()]
        self._def_fused(base_name, *values)
        for each in values:
            self.visit(each)

    @_dispatch(ForwardRef)
    def visit_forward_ref(self, node: ForwardRef):
        self.ios(node.name)

    @_dispatch(Primitive)
    def visit_primitive(self, node: Primitive):
        self.ios(node.typename)

    @_dispatch(Optional)
    def visit_opt(self, node: Optional):
        ios = self.ios
        existed = next((b for a, b in self.tmp_types if a == node), None)
        if existed:
            ios(existed)
            return
        tmp_name = "tmp%d" % id(node)

        if isinstance(node.typ, (Primitive, ForwardRef)):
            pass


def vector(typ: TypeSpec):
    pass
