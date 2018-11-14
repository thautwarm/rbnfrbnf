from rbnfrbnf.ir_constructs import *
from singledispatch import singledispatch
from typing import Dict
from functools import lru_cache
from Redy.Magic.Classic import record


class ContextForIR2:

    def __init__(self, imp: Dict[str, Identified], state=None):
        self.imp = imp
        self.recur = state or {None}
        self.resume = [lambda: None]
        self.perform = [lambda: None]

    def enter(self, name):
        self.perform.append(lambda: self.recur.add(name))
        self.resume.append(lambda: self.recur.remove(name))
        return self

    def __enter__(self):
        self.perform.pop()()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.resume.pop()()


@singledispatch
def terminate(node: Node, _):
    return node,


@terminate.register(NamedNonTerminal)
def _(node: NamedNonTerminal, ctx: ContextForIR2):
    name = node.name
    if name in ctx.recur:
        return node,

    with ctx.enter(name):

        return tuple(
            Chain(each, NoneTerminalEnd(name))
            for each in sum((terminate(each, ctx)
                             for each in ctx.imp[name].children), ()))


@terminate.register(Chain)
def _(node: Chain, ctx: ContextForIR2):
    ls = terminate(node.l, ctx)
    rs = terminate(node.r, ctx)
    return tuple(Chain(l, r) for l in ls for r in rs)


@terminate.register(Identified)
def _(node: Identified, ctx: ContextForIR2):


    res = []
    name = node.name
    with ctx.enter(name):
        for each in node.children:
            res.extend(terminate(each, ctx))
    res = [Chain(each, NoneTerminalEnd(name)) for each in res]
    ret = ctx.imp[name] = Identified(name, tuple(res))
    return ret
