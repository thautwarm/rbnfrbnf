"""
requires more infrastructures to implement fast GC ops in Cython.
// or simply use shared_ptr?
"""
import io


def struct(typename, actual_name=None, **fields):
    typename = typename.encode()
    fields = {k.encode(): (v1, v2.encode()) for k, (v1, v2) in fields.items()}

    with io.BytesIO() as ios:
        write = ios.write
        # c-struct: unboxed type
        write(b'cdef struct %s__unbox:\n' % typename)
        for field_name, (is_primitive, field_type) in fields.items():
            if is_primitive:
                write(b'    %s %s\n' % (field_type, field_name))
            else:
                write(b'    %s__unbox %s\n' % (field_type, field_name))
        write(b'\n')

        # python-class with statically linked fields
        write(b'@cython.final\n')
        write(b'cdef class %s:\n' % typename)
        write(b'    cdef %s__unbox _unbox\n' % typename)

        for field_name, (is_primitive, field_type) in fields.items():
            write(b'\n')
            # property: get/set from the unboxed.
            write(b'    property %s:\n' % field_name)
            if is_primitive:
                write(b'        def __get__(self): return self._unbox.%s\n' % field_name)
                write(b'        def __set__(self, %s value): self._unbox.%s = value\n' % (field_type, field_name))
            else:
                write(b'        def __get__(self): return %s._box(self._unbox.%s)\n' % (field_type, field_name))
                write(b'        def __set__(self, %s value): self._unbox.%s = value._unbox\n' % (
                field_type, field_name))

        # change what it boxed.
        write(b'    cdef void _box_of(self, %s__unbox ptr):\n' % typename)
        write(b'        self._unbox = ptr\n')
        write(b'\n')

        # make boxed instance from the unboxed.
        write(b'    @staticmethod\n')
        write(b'    cdef %s _box(%s__unbox ptr):\n'
              b'        this = %s()\n'
              b'        this._unbox = ptr\n'
              b'        return this\n' % (typename, typename, typename))
        write(b'\n')

        # convenient create method
        # TODO
        # write(b'    @staticmethod\n')
        # write(b'    cpdef %s new(')
        # for field_name, (is_primitive, field_type) in fields.items():
        #     write(' ')
        #     write(b'%s %s,'% (field_type, field_name))
        # write('):\n')
        # pretty format

        write(b'    def __repr__(self):\n')
        write(b'        cdef %s__unbox unbox = self._unbox\n' % typename)
        write(b'        with io.StringIO() as ios:\n')
        write(b'            write = ios.write\n')
        if actual_name:
            write(b'            write("%s{")\n' % actual_name.encode())
        else:
            write(b'            write("{")\n')

        for field_name, (is_primitive, field_type) in fields.items():
            attr = f"{field_name.decode()} = "
            attr = f"{attr!r}".encode()
            write(b'            write(%s)\n' % attr)
            if is_primitive:
                write(b'            write(repr(unbox.%s))\n' % field_name)
            else:
                write(b'            write(repr(%s._box(unbox.%s)))\n' % (field_type, field_name))
            write(b'            write(", ")\n')
        write(b'            write("}")\n')
        write(b'            return ios.getvalue()\n')
        write(b'\n')
        return ios.getvalue()


def adt(du_name: str, cases):
    du_name = du_name.encode()
    cases = [(k.encode(), v1, v2.encode()) for k, v1, v2 in cases]
    with io.BytesIO() as ios:
        write = ios.write
        write(b'cdef struct %s__unbox:\n' % du_name)
        write(b'    uint16_t tag\n')
        write(b'    void* variant\n')

        write(b'cdef class %s:\n' % du_name)
        write(b'    cdef %s__unbox _unbox\n' % du_name)

        for idx, (case_name, is_primitive, case_type) in enumerate(cases):
            write(b'    cpdef is%s(self): return self.tag == %d\n' % (case_name, idx))
            if is_primitive:
                write(b'    def as%s(self):\n'
                      b'        cdef %s* ptr = <%s*>(self._unbox.variant)\n'
                      b'        return ptr[0]\n' % (case_name, case_type, case_type))
            else:
                write(b'    def as%s(self):\n'
                      b'       cdef %s__unbox* ptr = <%s__unbox*>(self._unbox.variant)\n'
                      b'       return %s._box(ptr[0])\n' % (case_name, case_type, case_type, case_name))

        write(b'\n')
        return ios.getvalue()
