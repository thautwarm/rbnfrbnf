from rbnfrbnf.core.syntax_graph import Identified, SubRoutine, NamedTerminal, UnnamedTerminal, NonTerminalEnd, TerminalEnd, Dispatcher
from rbnfrbnf.core.tokenizer import Token, InternedString
from typing import List


def run_graph(tokens: List[Token], start: Identified):
    offset = 0
    fail_token = object()

    def call_subroutine(identified: Identified):
        nonlocal offset
        histories = offset, ()
        result = ()
        results = fail_token, ()
        push_stack = [iter(identified.starts)]

        current = None
        while push_stack:
            if current is None:
                current = next(push_stack[-1], None)

            if not current:
                push_stack.pop()
                offset, histories = histories
                result, results = results
                continue
            elif current is identified:
                return result

            ty = type(current)
            if ty is UnnamedTerminal:
                assert isinstance(current, UnnamedTerminal)
                try:
                    token = tokens[offset]
                except IndexError:
                    current = None
                    continue
                s1: InternedString = current.value
                s2 = token.value

                if (s2.i is 0 and s1.s == s2.s) or (s2.i == s1.i):

                    offset += 1
                    result = (token, result)
                    parent = current.parent
                    if parent:
                        current = parent
                    else:
                        break
                else:
                    current = None

            if ty is Dispatcher:
                assert isinstance(current, Dispatcher)
                histories = offset, histories
                results = result, results
                push_stack.append(iter(current.parents))
                current = None

            elif ty is NamedTerminal:
                try:
                    token = tokens[offset]
                except IndexError:
                    current = None
                    continue
                if current.typeid == token.type:
                    offset += 1
                    result = (token, result)
                    parent = current.parent
                    if parent:
                        current = parent
                    else:
                        break
                else:
                    current = None

            elif ty is TerminalEnd:
                assert isinstance(current, TerminalEnd)
                parent = current.parent
                if parent:
                    current = parent
                else:
                    break

            elif ty is NonTerminalEnd:
                assert isinstance(current, NonTerminalEnd)
                head = ()
                pack = current.pack
                if pack is 1:
                    # In shift-reduce algo, many pack num is 1,
                    # which could cause a severe performance problem.
                    # For above we do this corner case if-else.
                    sub_result, result = result
                    head = (sub_result, ())
                else:
                    for _ in range(pack):
                        sub_result, result = result
                        head = (sub_result, head)

                head = (current.name, head)
                result = (head, result)
                parent = current.parent
                if parent:
                    current = parent
                else:
                    break

            elif ty is SubRoutine:
                assert isinstance(current, SubRoutine)
                root = current.root
                sub_result = call_subroutine(root)
                if sub_result is not fail_token:
                    result = (root.name, sub_result), result
                    parent = current.parent
                    if parent:
                        current = parent
                    else:
                        break
                else:
                    current = None

        return result

    a = call_subroutine(start)
    if a:
        return start.name, a
    raise Exception
