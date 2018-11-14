from typing import Callable


class Until:

    def __init__(self, cond):
        self.cond = cond

    def __await__(self):
        cond = self.cond
        while not cond():
            yield


async def wait_for(some):
    await some


async def wait_until(some: Callable[[], bool]):
    await Until(some)
