from .types import *
from .load_cy import compile_module


def typespec_to_name(ty: TypeSpec):
    return unique_encode(str(ty))


class TypeAnalysis:
    types: t.Dict[str, TypeSpec]
    _mod: object

    def __init__(self):
        from .codegen import mk_types
        self.types = {}
        self._mod = None

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

    def mk_types(self) -> bytearray:
        raise NotImplementedError

    @property
    def mod(self):
        if not self._mod:
            self._mod = compile_module(self.mk_types(), 'parser')
        return self._mod

    def load_type(self, ty: t.Union[str, TypeSpec]):
        if isinstance(ty, str):
            ty = self.types[ty]

        return getattr(self.mod, typespec_to_name(ty))

    def load_constructor(self, ty: t.Union[str, TypeSpec],
                         constructor_name: str):
        if isinstance(ty, str):
            ty = self.types[ty]
        ty_mangled_name = typespec_to_name(ty)
        cons_mangled_name = "{0}_cons_{1}".format(ty_mangled_name,
                                                  constructor_name)
        return getattr(self.mod, cons_mangled_name)
