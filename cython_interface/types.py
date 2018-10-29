import typing as t

from .fast_template import *
from .load_cy import compile_module

K = t.TypeVar('K')
V = t.TypeVar('V')


class ImmutableMap(t.Mapping[K, V]):

    def __init__(self, **kwargs):
        self.tp = tuple(kwargs.items())

    def __iter__(self):
        for each, _ in self.tp:
            yield each

    def __len__(self) -> int:
        return len(self.tp)

    def __getitem__(self, k):
        try:
            return next(b for a, b in self.tp if a == k)
        except StopIteration:
            raise KeyError

    def map_values(self, f):
        new = ImmutableMap.__new__(ImmutableMap)
        new.tp = tuple((k, f(v)) for k, v in self.tp)
        return new

    def __hash__(self):
        return hash(self.tp)


class TypeSpec:
    pass


def _type_spec(cls):
    return type(cls.__name__, (cls, TypeSpec), {})


def unique_encode(string: str):
    # unique encoding

    return '_' + '_'.join(map(str, map(ord, string)))


def unique_decode(encoded: str):
    return ''.join(map(chr, map(int, encoded[1:].split('_'))))


@_type_spec
class ForwardRef(TypeSpec, t.NamedTuple):
    typename: str

    def __repr__(self):
        return self.typename


@_type_spec
class Primitive(TypeSpec, t.NamedTuple):
    typename: str

    def __repr__(self):
        return self.typename


@_type_spec
class TaggedUnion(TypeSpec, t.NamedTuple):

    args: t.Tuple[t.Tuple[str, TypeSpec], ...]

    def __repr__(self):
        return '|'.join(f'{case} of {ty!r}' for case, ty in self.args)


@_type_spec
class List(TypeSpec, t.NamedTuple):
    elem: TypeSpec

    def __repr__(self):
        return f'List<{self.elem!r}>'


@_type_spec
class Struct(TypeSpec, t.NamedTuple):
    fields: ImmutableMap[str, TypeSpec]

    def __repr__(self):
        fields = ','.join(f'{case} = {ty!r}' for case, ty in self.fields.tp)
        return f'{{{fields}}}'


@_type_spec
class Template(TypeSpec, t.NamedTuple):
    kind: str
    arguments: t.Tuple[TypeSpec, ...]

    def __repr__(self):
        arguments = ','.join(map(repr, self.arguments))
        return f'{self.kind}<{arguments}>'


LinkName = str
MangledName = str

_decl_buffer = b'''
# distutils: language = c++
from cython.operator cimport dereference, preincrement
from libc.stdint cimport uint16_t, uint32_t, uint64_t, int64_t, int32_t 
from libc.stdlib cimport malloc, free
from libcpp.memory cimport shared_ptr, make_shared
from libcpp.vector cimport vector
from libcpp.string cimport string
import io

ctypedef unsigned long size_t
cimport cython

'''


class CythonTypeManager:
    mod_name: str
    all_types: t.Dict[str, TypeSpec]
    generated_set: t.Set[MangledName]
    code_buffer: bytearray

    # template
    patterns: t.Dict[LinkName, t.Callable[[t.List[TypeSpec]], TypeSpec]]

    def lookup_type(self, name):
        return self.all_types[name]

    def __init__(self, mod_name='test'):
        self.mod_name = mod_name
        self._mod = None
        self.all_types = {}
        self.patterns = {}
        self.generated_set = {*()}
        self.code_buffer = bytearray()
        self.code_buffer += _decl_buffer

    def mk_cy_module(self):
        if not self._mod:
            self._codegen()
            code = self.code_buffer.decode()
            print(code)
            self._mod = compile_module(code, self.mod_name)
        return self._mod

    def load_var(self, name):
        return getattr(self._mod, unique_encode(str(self.lookup_type(name))))

    def is_generated(self, type_spec: TypeSpec):
        return unique_encode(str(type_spec)) in self.generated_set

    def define_type(self, name, spec: TypeSpec):
        if name in self.all_types:
            raise NameError("redefinition of typename %s" % name)
        self.all_types[name] = spec

    def define_template(self, name, spec_maker):
        if name in self.patterns:
            raise NameError("redefinition of template %s" % name)
        self.patterns[name] = spec_maker

    def _codegen(self):

        self.all_types = {
            k: self._expand_template(v)
            for k, v in self.all_types.items()
        }

        self.all_types = {
            k: self._resolve_type(v)
            for k, v in self.all_types.items()
        }

        for ty_name, each in self.all_types.items():
            self.mk_type(each, ty_name)

    def _expand_template(self, spec):

        def _expand(_):
            return self._expand_template(_)

        if isinstance(spec, (Primitive, ForwardRef)):
            return spec

        if isinstance(spec, TaggedUnion):
            return TaggedUnion(
                tuple((s, _expand(sub_spec)) for s, sub_spec in spec.args))

        if isinstance(spec, List):
            return List(_expand(spec.elem))

        if isinstance(spec, Struct):
            return Struct(spec.fields.map_values(_expand))

        if isinstance(spec, Template):
            return _expand(self.patterns[spec.kind](spec.arguments))

        raise TypeError

    def _resolve_type(self, spec: TypeSpec, recur=None):
        recur = recur or set()
        if spec in recur:
            return spec

        def _resolve(_):
            return self._resolve_type(_, {_, *recur})

        if isinstance(spec, ForwardRef):
            return _resolve(self.lookup_type(spec.typename))

        if isinstance(spec, Primitive):
            return spec

        if isinstance(spec, TaggedUnion):
            return TaggedUnion(
                tuple((s, _resolve(sub_spec)) for s, sub_spec in spec.args))
        if isinstance(spec, List):
            return List(_resolve(spec.elem))

        if isinstance(spec, Struct):
            return Struct(spec.fields.map_values(_resolve))

        raise TypeError

    def mk_type(self, spec: TypeSpec, name: t.Optional[str]) -> str:
        code_buffer = self.code_buffer

        if isinstance(spec, Primitive):
            return spec.typename
        if isinstance(spec, ForwardRef):
            typename = spec.typename
            spec = self.lookup_type(typename)
            return self.mk_type(spec, name)

        generated_set = self.generated_set
        ty_name = unique_encode(str(spec))
        if ty_name in generated_set:
            return ty_name
        generated_set.add(ty_name)
        if isinstance(spec, TaggedUnion):
            args = []
            for case_name, case_type in spec.args:
                args.append((case_name, isinstance(case_type, Primitive),
                             self.mk_type(case_type, case_name)))

                self.mk_type(case_type, name)
            code_buffer += adt(ty_name, args)
            return ty_name

        if isinstance(spec, List):
            elem_ty = spec.elem
            self.mk_type(elem_ty, name)
            elem_ty_name = unique_encode(str(elem_ty))
            code_buffer += vector(ty_name, elem_ty_name,
                                  isinstance(elem_ty, Primitive))
            return ty_name
        if isinstance(spec, Struct):
            fields = {
                k: (isinstance(v, Primitive), self.mk_type(v, None))
                for k, v in spec.fields.items()
            }
            code_buffer += struct(ty_name, name, **fields)
            return ty_name
        if isinstance(spec, Template):
            spec = self.patterns[spec.kind](spec.arguments)
            template_specialized = unique_encode(str(spec))
            code_buffer += b'ctypedef %s %s' % (template_specialized, ty_name)
            return ty_name
