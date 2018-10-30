from cython_interface2.analysis import *

ana = TypeAnalysis()
ana.define(
    'A',
    Struct(ImmutableMap.from_dict(a=Primitive('uint64_t'), b=ForwardRef('B'))))

ana.define('B', Struct(ImmutableMap.from_dict(c=Primitive('int64_t'))))

ana.define('Z',
           Tuple(SizedList.from_list([Primitive('int64_t'),
                                      ForwardRef('B')])))

ana.define(
    'U',
    TaggedUnion(
        ImmutableMap.from_dict(U_a=ForwardRef("B"), U_b=ForwardRef("A"))))

ana.resolve()
print(ana.mk_type().decode())
