from .types import *


def typespec_to_name(ty: TypeSpec):
    return unique_encode(str(ty))


class TypeAnalysis:
    types: t.Dict[str, TypeSpec]

    def __init__(self):
        from .codegen import mk_type
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

    def mk_type(self) -> bytearray:
        raise NotImplementedError
