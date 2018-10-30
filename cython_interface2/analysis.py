from .types import *


def _to_name(ty: TypeSpec):
    return unique_encode(str(ty))


class TypeAnalysis:
    types: t.Dict[str, TypeSpec]

    def __init__(self):
        self.types = {}

    def define(self, name: str, ty: TypeSpec):
        if name in self.types:
            raise NameError('redefinition of %s' % name)
        self.types[name] = ty

    def resolve(self) -> t.NoReturn:
        types = self.types
        empty = set()

        def resolve_rec(ty, recur=None):

            def _resolve(ty):
                return resolve_rec(ty, {*recur, ty})

            recur = recur or empty
            if ty in recur:
                return ty
            if isinstance(ty, ForwardRef):
                return _resolve(types[ty.typename])
            if isinstance(ty, Primitive):
                return ty
            if isinstance(ty, TaggedUnion):
                return TaggedUnion(ty.args.map_values(_resolve))
            if isinstance(ty, List):
                return List(resolve_rec(ty.elem))
            if isinstance(ty, Tuple):
                return Tuple(ty.elems.map(_resolve))
            if isinstance(ty, Struct):
                return Struct(ty.fields.map_values(_resolve))
            raise TypeError

        self.types = {k: resolve_rec(v) for k, v in types.items()}

    def mk_type(self):
        buf = bytearray()

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

            mangled_name = _to_name(ty)
            if mangled_name in generated_set:
                return mangled_name

            generated_set.add(mangled_name)
            # tagged union generator
            if isinstance(ty, TaggedUnion):
                name = name or '<anonymous-union>'  # for __repr__

                def map_act(i: int, case_name: str, case_ty: TypeSpec):
                    return i, case_name, mk_type_rec(case_ty, case_name)

                pairs = ty.args.to_list().map2i(map_act)
                write(f'{mangled_name}_caselst = [')

                @pairs.iter
                def _(tp):
                    mangled_case_name = tp[2]
                    write(mangled_case_name)
                    write(b', ')

                write(b']\n')

                @pairs.iter
                def _(tp):
                    # make constructor
                    i, _, mangled_case_name = tp
                    write('cpdef {0}_cons_{1}({0} obj):\n'.format(
                        mangled_case_name, mangled_name))
                    write(
                        'cdef %s inst = %s()\n' % (mangled_name, mangled_name),
                        indent=2)
                    write(b'inst.tag = %d\n' % i, indent=2)
                    write(b'inst.obj = obj\n', indent=2)
                    write(b'return inst\n', indent=2)

                write("cdef class %s:\n" % mangled_name)
                write(b'cdef int8_t tag\n', indent=2)
                write(b'cdef object obj\n', indent=2)

                @pairs.iter
                def _(tp):
                    # make destructor
                    i, case_name, mangled_case_name = tp
                    write('cpdef is%s(self):\n' % case_name, indent=2)
                    write(b'return self.tag == %d\n\n' % i, indent=4)
                    write(
                        'cpdef %s as%s(self):\n' % (mangled_case_name,
                                                    case_name),
                        indent=2)
                    write('return self.obj\n\n', indent=4)

                write('cpdef case_of(self, dict type_map_f):\n', indent=2)
                write(
                    f'return type_map_f[{mangled_name}_caselst[self.tag]](self.obj)\n\n',
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

                for i in range(len(elem_typenames)):
                    write(f'self._{i} = _{i}\n', indent=4)

                return mangled_name

            if isinstance(ty, Struct):

                def map_act(field_name: str, field_type: TypeSpec):
                    return field_name, mk_type_rec(field_type)

                triples = ty.fields.to_list().map2(map_act)
                write(f'cdef class {mangled_name}:\n')

                @triples.iter2
                def _(field_name: str, m_field_typename: str):
                    write(
                        f'cdef public {m_field_typename} {field_name}\n',
                        indent=2)

                write(b'def __init__(self, ', indent=2)

                @triples.iter2
                def _(field_name: str, elem_typename: str):
                    write(f'{elem_typename} {field_name}, ')
                    pass

                write(b'):\n')

                @triples.iter2
                def _(field_name: str, _: str):
                    write(f'self.{field_name} = {field_name}\n', indent=4)

                return mangled_name

        for name, each in self.types.items():
            mk_type_rec(each, name)

        return buf
