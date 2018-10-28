def vector(typename):
    return f"""
cdef class {typename}Vector:
    cdef vector[{typename}] _c
    
    def __len__(self):
        return self._c.size()
    
    def __getitem__(self, size_t idx):
        return self._c[idx]
        
    def append(self, {typename} obj):
        self._c.push_back(obj)
    
    def pop(self):
        return self._c.pop_back()
    
    def insert(self, size_t pos, {typename} obj):
        c = self._c
        c.insert(c.begin() + pos, obj)
    
    def __repr__(self):
        
        with io.StringIO() as s:
            write = s.write
            write("{typename}Vector[")
            for each in self._c:
                write(str(each))
                write(", ")
            write("]")
            return s.getvalue()        
"""

