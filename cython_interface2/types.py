import typing as t
from .meta_level_types import SizedList, ImmutableMap


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
    args: ImmutableMap[str, TypeSpec]

    def __repr__(self):
        cases = ','.join(f'{ty!r}' for case, ty in self.args.items())
        return f'Union[{cases}]'


@_type_spec
class List(TypeSpec, t.NamedTuple):
    elem: TypeSpec

    def __repr__(self):
        return f'List[{self.elem!r}]'


@_type_spec
class Tuple(TypeSpec, t.NamedTuple):
    elems: SizedList[TypeSpec]

    def __repr__(self):
        fields = ','.join(f'{ty!r}' for ty in self.elems.tp)
        return f'Tuple[{fields}]'


@_type_spec
class Struct(TypeSpec, t.NamedTuple):
    fields: ImmutableMap[str, TypeSpec]

    def __repr__(self):
        fields = ','.join(f'{case} = {ty!r}' for case, ty in self.fields.tp)
        return f'{{{fields}}}'
