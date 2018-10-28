import typing as t


class State:
    traceback: t.List[int]
    nodes: t.List[t.Any]
    actions: t.List[t.Callable]

    @property
    def current_token_num(self):
        return self.traceback[-1]

    @current_token_num.setter
    def current_token_num(self, value):
        self.traceback[-1] = value
