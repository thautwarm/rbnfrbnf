from rbnfrbnf.ir_constructs import *
from rbnfrbnf.resolving_utils import *
from rbnfrbnf.utils import *
from singledispatch import singledispatch
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
                    isinstance(_, NoneTerminalEnd) for _ in each):
                raise Exception("Endless left recursion.")
            yield (LeftRecur(), *each)
        else:
            yield each


def unique(identified: Identified):
    children = tuple(
        tuple(flatten(each, test_fn)) for each in identified.children)

    pool = set()
    res = []
    for each in children:
        if each not in pool:
            pool.add(each)
            res.append(each)

    name = identified.name
    return name, tuple(mark_left_recur(name, res))


def _group_by(stream):
    res = defaultdict(list)
    for each in stream:
        res[each[0]].append(each[1:])
    return res


def merge(lst: Tuple[Tuple[Node, ...], ...]) -> tuple:

    if len(lst) is 1:
        return reduce(Chain, lst[0]),
    groups = _group_by(lst)

    def process_optional(each):
        n1 = len(each)
        each = list(_ for _ in each if _)
        n2 = len(each)
        if n1 < n2:
            each.append(TerminalEnd())
        return tuple(each)

    return tuple(
        MultiParents(k, merge(process_optional(v))) if v else k
        for k, v in groups.items())


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
        self.all_nodes = {*self.identified_nodes.values()}

    def set_current_identified(self, name: str):
        self.current_identifier = name

    def get_identified(self, name) -> syntax_graph.Identified:
        return self.identified_nodes[name]


@singledispatch
def build_graph(node, _) -> List[syntax_graph.Node]:
    raise TypeError


@build_graph.register(Identified)
def _(node: Identified, ctx: ContextForIR3):
    name = node.name
    ctx.set_current_identified(name)
    n = ctx.get_identified(name)
    subs = sum([build_graph(child, ctx) for child in node.children], [])
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


@build_graph.register(NoneTerminalEnd)
def _(node: NoneTerminalEnd, ctx: ContextForIR3):
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
