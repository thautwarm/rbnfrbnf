from rbnfrbnf.ir_constructs import *
from rbnfrbnf.resolving_utils import *
from rbnfrbnf.utils import *
from rbnfrbnf import syntax_graph
from typing import Dict, List, Tuple
from collections import defaultdict
from functools import reduce
from rbnfrbnf.tokenizer import InternedString


def test_fn(elem):
    if isinstance(elem, Chain):
        return True, (elem.l, elem.r)
    return False, None


def mark_left_recur(name, lst_of_lst):
    for each in lst_of_lst:
        e = each[0]
        if isinstance(e, NamedNonTerminal) and e.name == name:
            each = each[1:]
            if len(each) is 0 or all(
                    isinstance(_, NonTerminalEnd) for _ in each):
                raise Exception("Endless left recursion.")
            yield (LeftRecur(), *each)
        else:
            yield each


def unique(identified: Identified):

    children = tuple(
        tuple(flatten([each], test_fn)) for each in identified.children)

    pool = set()
    res = []
    for each in children:
        if each not in pool:
            pool.add(each)
            res.append(each)

    name = identified.name
    res = tuple(mark_left_recur(name, res))
    return name, res


_terminal_end = TerminalEnd()


def _group_by(stream):
    res = defaultdict(list)
    for each in stream:
        if not each:
            res[_terminal_end] = [()]
        else:
            res[each[0]].append(each[1:])
    return res


def process_optional(seq):
    n1 = len(seq)
    seq = list(_ for _ in seq if _)
    n2 = len(seq)
    if n1 > n2:
        seq.append([TerminalEnd()])
    return seq


def merge(lst) -> tuple:
    lst = process_optional(lst)
    if len(lst) is 1:
        return reduce(Chain, lst[0]),
    groups = _group_by(lst)

    def _():
        for k, v in groups.items():
            if v:
                yield MultiParents(k, merge(v))
            else:
                yield k

    return tuple(_())


def prune(identified_lst: List[Identified]):
    identified_lst = tuple(map(unique, identified_lst))
    return [
        Identified(name, merge(children)) for name, children in identified_lst
    ]


class ContextForIR3:

    def __init__(self, token_typeids: dict, identified_node_names):
        self.token_typeids = token_typeids
        self.identified_nodes: Dict[str, syntax_graph.Identified] = {
            name: syntax_graph.Identified(name)
            for name in identified_node_names
        }
        self.current_identifier: str = None
        all_nodes = self.all_nodes = OrderedSet()
        for each in self.identified_nodes.values():
            all_nodes.add(each)

    def set_current_identified(self, name: str):
        self.current_identifier = name

    def get_identified(self, name) -> syntax_graph.Identified:
        return self.identified_nodes[name]


def overload(f):

    dispatcher = {}

    def dispatch(arg, *args, **kwargs):
        app = dispatcher.get(type(arg)) or f
        return app(arg, *args, **kwargs)

    def register(ty):

        def app(g):
            dispatcher[ty] = g
            return g

        return app

    dispatch.register = register
    return dispatch


@overload
def build_graph(node, _) -> List[syntax_graph.Node]:
    raise TypeError


@build_graph.register(TerminalEnd)
def _(_, __):
    return [syntax_graph.TerminalEnd()]


@build_graph.register(Identified)
def _(node: Identified, ctx: ContextForIR3):
    name = node.name
    ctx.set_current_identified(name)
    n = ctx.get_identified(name)

    def _():
        for child in node.children:
            yield from build_graph(child, ctx)

    subs = _()
    for sub in subs:
        sub.as_child_of(n)

    n.starts = syntax_graph.get_leaves(n)
    return [n]


@build_graph.register(UnnamedTerminal)
def _(node: UnnamedTerminal, ctx: ContextForIR3):
    node = syntax_graph.UnnamedTerminal(InternedString.make(node.value))
    ctx.all_nodes.add(node)
    return [node]


@build_graph.register(NamedTerminal)
def _(node: NamedTerminal, ctx: ContextForIR3):
    name = node.name
    node = syntax_graph.NamedTerminal(ctx.token_typeids[name], name)
    ctx.all_nodes.add(node)
    return [node]


@build_graph.register(NamedNonTerminal)
def _(node: NamedTerminal, ctx: ContextForIR3):
    name = node.name
    node = syntax_graph.SubRoutine(ctx.get_identified(name))
    ctx.all_nodes.add(node)
    return [node]


@build_graph.register(Chain)
def _(node: Chain, ctx: ContextForIR3):
    if isinstance(node.l, LeftRecur):
        lrs = build_graph(node.r, ctx)
        identifier = ctx.current_identifier
        n = ctx.get_identified(identifier)
        for lr in syntax_graph.get_leaves(*lrs):
            n.as_child_of(lr)
        return lrs

    lefts = build_graph(node.l, ctx)
    rights = build_graph(node.r, ctx)
    for right in syntax_graph.get_leaves(*rights):
        for left in lefts:
            left.as_child_of(right)
    return rights


@build_graph.register(NonTerminalEnd)
def _(node: NonTerminalEnd, ctx: ContextForIR3):
    node = syntax_graph.NonTerminalEnd(node.name)
    ctx.all_nodes.add(node)
    return [node]


@build_graph.register(MultiParents)
def _(node: MultiParents, ctx: ContextForIR3):
    targets = sum([build_graph(each, ctx) for each in node.targets], [])
    if isinstance(node.root, LeftRecur):
        lrs = targets
        identifier = ctx.current_identifier
        n = ctx.get_identified(identifier)
        for lr in syntax_graph.get_leaves(*lrs):
            n.as_child_of(lr)
        return lrs

    roots = build_graph(node.root, ctx)
    for target in syntax_graph.get_leaves(*targets):
        for root in roots:
            root.as_child_of(target)

    return targets
