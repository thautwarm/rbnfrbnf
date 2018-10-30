import typing as t

K = t.TypeVar('K')
V = t.TypeVar('V')

T = t.TypeVar('T')
G = t.TypeVar('G')


class ImmutableMap(t.Mapping[K, V]):

    @classmethod
    def from_dict(cls, *args, **kwargs):
        return cls(tuple(dict(*args, **kwargs).items()))

    def __init__(self, tp: t.Tuple[t.Tuple[K, V], ...]):
        self.tp = tp

    def __iter__(self):
        for each, _ in self.tp:
            yield each

    def __len__(self) -> int:
        return len(self.tp)

    def __getitem__(self, k):
        try:
            return next(b for a, b in self.tp if a == k)
        except StopIteration:
            raise KeyError

    def iter(self, f: t.Callable[[K, V], t.NoReturn]) -> t.NoReturn:
        for k, v in self.tp:
            f(k, v)

    def map(self,
            f: t.Callable[[K, V], t.Tuple[T, G]]) -> 'ImmutableMap[T, G]':
        new = ImmutableMap.__new__(ImmutableMap)
        new.tp = tuple(f(k, v) for k, v in self.tp)
        return new

    def mapi(self, f: t.Callable[[int, K, V], t.Tuple[T, G]]
             ) -> 'ImmutableMap[T, G]':
        return ImmutableMap(
            tuple(f(i, k, v) for i,
                  (k, v) in enumerate(self.tp)))

    def map_values(self, f: t.Callable[[V], T]) -> 'ImmutableMap[K, T]':
        return ImmutableMap(tuple((k, f(v)) for k, v in self.tp))

    def iter_values(self, f: t.Callable[[V], t.NoReturn]) -> t.NoReturn:
        for k, v in self.tp:
            f(v)

    def map_keys(self, f: t.Callable[[K], T]) -> 'ImmutableMap[T, V]':

        return ImmutableMap(tuple((f(k), v) for k, v in self.tp))

    def iter_keys(self, f: t.Callable[[K], t.NoReturn]) -> t.NoReturn:
        for k, v in self.tp:
            f(k)

    def to_list(self) -> 'SizedList[t.Tuple[K, V]]':
        return SizedList(self.tp)

    def __hash__(self):
        return hash(self.tp)


class SizedList(t.Generic[T]):
    tp: t.Tuple[T, ...]

    @classmethod
    def from_list(cls, *args):
        return cls(tuple(*args))

    def __init__(self, tp: t.Tuple[T, ...]):
        self.tp = tp

    def __getitem__(self, item):
        return self.tp[item]

    def __len__(self):
        return len(self.tp)

    def __repr__(self):
        return repr(self.tp)

    def __iter__(self):
        yield from self.tp

    def iter(self, f):
        for e in self.tp:
            f(e)

    def iteri(self, f):
        for i, e in enumerate(self.tp):
            f(i, e)

    def map(self, f: t.Callable[[T], G]):
        return SizedList(tuple(f(e) for e in self.tp))

    def mapi(self, f: t.Callable[[int, T], G]):
        return SizedList(tuple(f(i, e) for i, e in enumerate(self.tp)))

    def iter2(self, f):
        for a, b in self.tp:
            f(a, b)

    def map2(self: 'SizedList[t.Tuple[K, V]]',
             f: t.Callable[[K, V], G]) -> 'SizedList[G]':
        return SizedList(tuple(f(k, v) for k, v in self.tp))

    def map2i(self: 'SizedList[t.Tuple[K, V]]',
              f: t.Callable[[int, K, V], G]) -> 'SizedList[G]':
        return SizedList(tuple(f(i, k, v) for i, (k, v) in enumerate(self.tp)))

    def to_im_map(self):
        return ImmutableMap(self.tp)
