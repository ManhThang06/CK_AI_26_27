"""Rang buoc cua Kakuro. Mot run (day o trang lien tiep) la rang buoc bac cao Sum + Alldiff,
nen loc mien bang bang to hop chu so thay vi AC-3 nhi phan."""
from abc import ABC, abstractmethod
from itertools import combinations
from typing import NamedTuple


class CombinationTable:
    """Bang (so o k, tong S) -> cac tap k chu so khac nhau tu 1..9 co tong S."""

    def __init__(self):
        self._table = {}
        for k in range(1, 10):
            for digits in combinations(range(1, 10), k):
                self._table.setdefault((k, sum(digits)), []).append(frozenset(digits))

    def lookup(self, size, total):
        return self._table.get((size, total), [])



class RunState(NamedTuple):
    """Trang thai mot run theo cac mien hien tai (dung chung cho loc mien va UI).

    used    cac chu so cua o da xac dinh (mien 1 gia tri)
    free    cac o chua xac dinh
    rest    tong con lai can dat bang cac o free
    combos  cac tap chu so hop le: dung len(free) chu so khac nhau, tong = rest,
            khong trung used, va nam trong hop mien cua cac o free
    """
    used: list
    free: list
    rest: int
    combos: list


class Constraint(ABC):
    def __init__(self, name, cells):
        self.name = name              # vd "A1" (ngang), "D2" (doc)
        self.cells = tuple(cells)     # cac Cell theo thu tu

    @abstractmethod
    def filter(self, domains, removed):
        """Loc mien, ghi cac Removal vao `removed`. Tra ve cac o bi thu hep mien, hoac None
        neu rang buoc khong the thoa."""

    @abstractmethod
    def is_satisfied_by(self, values):
        """values: gia tri day du cua cac o, theo thu tu `cells`."""


class Run(Constraint):
    COMBINATIONS = CombinationTable()

    def __init__(self, name, cells, total):
        super().__init__(name, cells)
        self.total = total

    @property
    def size(self):
        return len(self.cells)

    def is_feasible(self):
        """Co the dat tong bang `size` chu so khac nhau tu 1..9 hay khong."""
        k = self.size
        return k <= 9 and k * (k + 1) // 2 <= self.total <= sum(range(10 - k, 10))

    def state(self, domains):
        used = [domains.value(c) for c in self.cells if domains.is_fixed(c)]
        free = [c for c in self.cells if not domains.is_fixed(c)]
        rest = self.total - sum(used)
        combos = []
        if free:
            used_set = set(used)
            reachable = set().union(*(domains[c] for c in free))
            combos = [combo for combo in self.COMBINATIONS.lookup(len(free), rest)
                      if not combo & used_set and combo <= reachable]
        return RunState(used, free, rest, combos)

    def filter(self, domains, removed):
        used, free, rest, combos = self.state(domains)
        if len(set(used)) < len(used):
            return None                              # hai o trung chu so
        if not free:
            return [] if rest == 0 else None
        allowed = set().union(*combos)
        if not allowed:
            return None
        changed = []
        for cell in free:
            for value in sorted(domains[cell] - allowed):
                domains.remove(cell, value, self.name, removed)
                if cell not in changed:
                    changed.append(cell)
            if not domains[cell]:
                return None
        return changed

    def is_satisfied_by(self, values):
        return (all(type(v) is int and 1 <= v <= 9 for v in values)
                and len(set(values)) == len(values) and sum(values) == self.total)
