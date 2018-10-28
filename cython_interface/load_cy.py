import tempfile
import os
import subprocess
from importlib import util
from string import Template

template = Template(r"""
from distutils.core import setup
from Cython.Build import cythonize
setup(ext_modules=cythonize([$module]))
""")


def compile_module(source_code: str, mod_name: str):
    # TODO:
    # tempfile.TemporaryDirectory will close unexpectedly before removing the generated module.
    # Since that we don't delete the temporary dir as a workaround.
    mod_name = 'cythonextension_' + mod_name

    dirname = tempfile.mkdtemp()
    mod_path = mod_name + '.pyx'
    with open(os.path.join(dirname, mod_path), 'w') as pyx_file, open(
            os.path.join(dirname, 'setup.py'), 'w') as setup_file:
        pyx_file.write(source_code)
        setup_file.write(template.substitute(module=repr(mod_path)))

    cwd = os.getcwd()
    os.chdir(dirname)
    subprocess.check_call(['python', 'setup.py', 'build_ext', '--inplace'])
    os.chdir(cwd)
    pyd_name = next(
        each for each in os.listdir(dirname) if each.endswith('.pyd'))
    spec = util.spec_from_file_location(mod_name,
                                        os.path.join(dirname, pyd_name))
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

code = f"""
# distutils: language = c++
from libc.stdint cimport uint32_t, uint64_t, int64_t 
from libcpp.vector cimport vector
from libcpp.string cimport string
import io

ctypedef unsigned long size_t
cimport cython

cdef struct __G:
    int flag


cdef class G:
    cdef __G __
    def __init__(self, int flag):
        self.__.flag = flag
        
    
    property flag:
        def __get__(self):
            return self.__.flag
        
        def __set__(self, value: int):
            self.__.flag = value

ctypedef int64_t Int 

"""

mod = compile_module(code, 'test')
print(mod.__dict__.keys())

g = mod.G(2)

