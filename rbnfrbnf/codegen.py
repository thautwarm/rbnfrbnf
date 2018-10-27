from .constructs import *
from python_passes.utils import visitor


@visitor
class CodeGen(ast.NodeVisitor):
    def __init__(self, ios=print):
        self.ios = ios
