import ast
from copy import deepcopy


def to_pascal(name: str):
    return ''.join(map(str.capitalize, name.split('_')))


def visitor(cls: type):
    to_update = []
    for attr, member in cls.__dict__.items():
        if attr.startswith('visit_'):
            to_update.append(('visit_' + to_pascal(attr[6:]), member))
    for attr, member in to_update:
        setattr(cls, attr, member)
    return cls


@visitor
class _ArgCollector(ast.NodeVisitor):
    def __init__(self):
        self.args = []

    def visit_arg(self, arg: ast.arg):
        self.args.append(arg.arg)


def function_args(node: ast.FunctionDef):
    collector = _ArgCollector()
    collector.visit(node.args)
    return collector.args


@visitor
class _SubstitutionExecutor(ast.NodeVisitor):
    def __init__(self, mapping):
        self.mapping = mapping

    def visit_name(self, node: ast.Name):
        _ = self.mapping.get(node.id)
        if _:
            node.id = _

    def visit_except_handler(self, node: ast.ExceptHandler):
        _ = self.mapping.get(node.name)
        if _:
            node.name = _


def substitute(node: ast.AST, mapping: dict):
    executor = _SubstitutionExecutor(mapping)
    node = deepcopy(node)
    executor.visit(node)
    return node