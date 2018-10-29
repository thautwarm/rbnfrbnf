from cython_interface.types import *

manager = CythonTypeManager()

# manager.define_type(
#     'S', Struct(ImmutableMap(a=Primitive('int64_t'), b=Primitive('int32_t'))))
#
# manager.define_type(
#     'X', Struct(ImmutableMap(a=Template('Tuple', (Primitive('int64_t'), )))))
#
# manager.define_type('T',
#                     Template('Tuple', (Primitive('int64_t'), ForwardRef('X'))))
#
# manager.define_template('Tuple',
#                         lambda ty_lst:
#                         Struct(ImmutableMap(**{f'_{idx + 1}': ty for idx, ty in enumerate(ty_lst)})))
#
manager.define_type('U', Struct(ImmutableMap(s=Primitive('string'))))
# manager.define_type(
#     'A',
#     TaggedUnion((('A_1', Primitive('int64_t')), ('A_2', Primitive('char*')))))
manager.mk_cy_module()

U = manager.load_var('U')



