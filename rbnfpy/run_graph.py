from .syntax_graph import Node, Identified, SubRoutine, NamedTerminal, UnnamedTerminal, NonTerminalEnd
from .tokenizer import Token, InternedString
from typing import List
from collections import deque


class State:
    tokens: List[Token]
    offset: int


def make_token(s: str, t: int = 0):
    return Token(0, 1, 2, 'sss', t, InternedString(s))


def run_graph(tokens: List[Token], start: Identified):
    offset = 0
    histories = (0, ())
    results = ()

    def call_subroutine(identified: Identified):
        nonlocal offset, histories, results
        result = ()
        envs = [iter(identified.starts)]
        while envs:
            current = next(envs[-1], None)
            if not current:
                # resume
                envs.pop()
                continue
            ty = type(current)

            if ty is UnnamedTerminal:
                try:
                    token = tokens[offset]
                except IndexError:
                    return results
                s1: InternedString = current.value
                s2 = token.value
                if (s2.i is 0 and s1.s == s2.s) or (s2.i == s1.i):
                    offset += 1
                    results = result, results
                    result = ()
                    envs.append(iter(current.parents))
                    continue
                else:
                    # resume
                    envs.pop()
                    offset, histories = histories
                    result, results = results
                    continue
            elif ty is NamedTerminal:
                try:
                    token = tokens[offset]
                except IndexError:
                    return results

                if current.typeid == token.type:
                    offset += 1
                    results = result, results
                    result = ()
                    envs.append(iter(current.parents))
                    continue
                else:
                    # resume
                    envs.pop()
                    offset, histories = histories
                    result, results = results
                    continue
            elif ty is NonTerminalEnd:
                result = current.name, result
                envs.append(iter(current.parents))
                continue
            elif ty is SubRoutine:
                assert isinstance(current, SubRoutine)
                results = call_subroutine(current.root)
                continue
        # results = result, results
        return results

    return call_subroutine(start)
