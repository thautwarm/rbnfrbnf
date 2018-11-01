from .analysis import *
from .load_cy import compile_module
import os
import cython_imports


def mk_type(self: TypeAnalysis):
    with open(
            os.path.join(
                os.path.split(cython_imports.__file__)[0], 'lexer.pyx'),
            'rb') as _:
        buf = bytearray(_.read())

    def write(bs, indent=0):
        nonlocal buf
        if type(bs) is str:
            bs = bs.encode()
        for i in range(indent):
            buf += b' '
        buf += bs

    generated_set: t.Set[bytes] = set()
    types = self.types

    def mk_type_rec(ty, name=None) -> str:
        if isinstance(ty, Primitive):
            return ty.typename

        if isinstance(ty, ForwardRef):
            typename = ty.typename
            ref_ty = types[typename]
            return mk_type_rec(ref_ty, typename)

        mangled_name = typespec_to_name(ty)
        if mangled_name in generated_set:
            return mangled_name

        generated_set.add(mangled_name)
        # tagged union generator
        if isinstance(ty, TaggedUnion):
            name = name or '<anonymous-union>'  # for __repr__

            def map_act(i: int, case_name: str, case_ty: TypeSpec):
                return i, case_name, mk_type_rec(case_ty, case_name)

            pairs = ty.args.to_list().map2i(map_act)
            write(f'{mangled_name}_casetype_lst = [')

            @pairs.iter
            def _(tp):
                mangled_case_name = tp[2]
                write(mangled_case_name)
                write(b', ')

            write(b']\n')

            write(f'{mangled_name}_casename_lst = [')

            @pairs.iter
            def _(tp):
                case_name = tp[1]
                write(repr(case_name))
                write(b', ')

            write(b']\n')

            @pairs.iter
            def _(tp):
                # make constructor
                i, _, mangled_case_name = tp
                write('cpdef {0}_cons_{1}_{2}({0} obj):\n'.format(
                    mangled_case_name, mangled_name, i))
                write(
                    'cdef %s inst = %s()\n' % (mangled_name, mangled_name),
                    indent=2)
                write(b'inst.tag = %d\n' % i, indent=2)
                write(b'inst.obj = obj\n', indent=2)
                write(b'return inst\n', indent=2)

            write("cdef class %s:\n" % mangled_name)
            write(b'cdef int8_t tag\n', indent=2)
            write(b'cdef object obj\n', indent=2)

            write(b'def __repr__(self):\n', indent=2)
            write(
                f'   return "{name}.{{}}({{!r}})".'
                f'format({mangled_name}_casename_lst[self.tag], self.obj)\n',
                indent=4)
            write(b'def __hash__(self):\n', indent=2)
            write(b'return (self.tag + 10086) ^ hash(self.obj)\n', indent=4)

            @pairs.iter
            def _(tp):
                # make destructor
                i, case_name, mangled_case_name = tp
                write('cpdef is%s(self):\n' % case_name, indent=2)
                write(b'return self.tag == %d\n\n' % i, indent=4)
                write(
                    'cpdef %s as%s(self):\n' % (mangled_case_name, case_name),
                    indent=2)
                write('return self.obj\n\n', indent=4)

            write('cpdef case_of(self, dict type_map_f):\n', indent=2)
            write(
                f'return type_map_f[{mangled_name}_casetype_lst[self.tag]](self.obj)\n\n',
                indent=4)

            return mangled_name

        if isinstance(ty, List):
            mk_type_rec(ty.elem)
            # TODO, strongly typed list?
            return 'list'

        if isinstance(ty, Tuple):
            elem_typenames = ty.elems.map(mk_type_rec)
            write('cdef class %s:\n' % mangled_name)

            @elem_typenames.iteri
            def _(i: int, elem_typename: str):
                write(f'cdef readonly {elem_typename} _{i}\n', indent=2)

            write(b'def __init__(self,', indent=2)

            @elem_typenames.iteri
            def _(i: int, elem_typename: str):
                write(f'{elem_typename} _{i}, ')
                pass

            write(b'):\n')
            if not elem_typenames:
                write(f'pass\n', indent=4)
            else:
                for i in range(len(elem_typenames)):
                    write(f'self._{i} = _{i}\n', indent=4)

            render_template = ["{}"] * len(elem_typenames)
            render_template = ', '.join(render_template)
            elem_list_template = ', '.join(
                f'self._{i}' for i in range(len(elem_typenames)))
            render_template = '"({})".format({})'.format(
                render_template, elem_list_template)
            write(b'def __repr__(self):\n', indent=2)
            write(f'return {render_template}\n', indent=4)

            write(b'def __hash__(self):\n')
            write(f'return hash(({elem_list_template},))\n', indent=4)

            return mangled_name

        if isinstance(ty, Struct):

            def map_act(field_name: str, field_type: TypeSpec):
                return field_name, mk_type_rec(field_type)

            triples = ty.fields.to_list().map2(map_act)
            write(f'cdef class {mangled_name}:\n')

            @triples.iter2
            def _(field_name: str, m_field_typename: str):
                write(
                    f'cdef public {m_field_typename} {field_name}\n', indent=2)

            write(b'def __init__(self, ', indent=2)

            @triples.iter2
            def _(field_name: str, elem_typename: str):
                write(f'{elem_typename} {field_name}, ')
                pass

            write(b'):\n')

            @triples.iter2
            def _(field_name: str, _: str):
                write(f'self.{field_name} = {field_name}\n', indent=4)

            if not len(triples):
                write(f'pass\n', indent=4)

            return mangled_name

    for name, each in self.types.items():
        mk_type_rec(each, name)

    return buf


def mk_mod(code: bytearray):
    return compile_module(code, 'parser')


TypeAnalysis.mk_type = mk_type
