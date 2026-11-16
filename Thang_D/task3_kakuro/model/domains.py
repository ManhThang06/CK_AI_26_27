"""Domains: mien gia tri cua moi bien, kem cac thao tac loai / hoan tac co ghi vet."""
from typing import NamedTuple

from .cell import Cell


class Removal(NamedTuple):
    """Mot gia tri bi loai khoi mien: o nao, gia tri nao, do run nao (hoac "assign")."""
    cell: Cell
    value: int
    reason: str


class Domains:
    DIGITS = range(1, 10)

    def __init__(self, mapping):
        self._sets = {cell: set(values) for cell, values in mapping.items()}

    @classmethod
    def full(cls, cells):
        """Moi o bat dau voi mien {1..9}."""
        return cls({cell: cls.DIGITS for cell in cells})

    @classmethod
    def from_snapshot(cls, snapshot):
        """Dung lai tu anh chup {"r,c": [gia tri]} (xem snapshot)."""
        return cls({Cell.parse(key): values for key, values in snapshot.items()})

    # ------------------------------------------------------------ doc
    def __getitem__(self, cell):
        return self._sets[cell]

    def __iter__(self):
        return iter(self._sets)

    def __len__(self):
        return len(self._sets)

    def __contains__(self, cell):
        return cell in self._sets

    def __eq__(self, other):
        if isinstance(other, Domains):
            other = other._sets
        return self._sets == dict(other)

    __hash__ = None

    def items(self):
        return self._sets.items()

    def size(self, cell):
        return len(self._sets[cell])

    def is_fixed(self, cell):
        return len(self._sets[cell]) == 1

    def value(self, cell):
        """Gia tri duy nhat cua o da xac dinh."""
        return next(iter(self._sets[cell]))

    def unassigned(self):
        """Cac o chua xac dinh (mien tu 2 gia tri tro len)."""
        return [cell for cell, values in self._sets.items() if len(values) > 1]

    def empty_cells(self):
        return sorted(cell for cell, values in self._sets.items() if not values)

    def snapshot(self):
        return {cell.key: sorted(self._sets[cell]) for cell in sorted(self._sets)}

    def copy(self):
        return Domains(self._sets)

    # ------------------------------------------------------------ ghi
    def remove(self, cell, value, reason, log):
        self._sets[cell].discard(value)
        log.append(Removal(cell, value, reason))

    def fix(self, cell, value, log, reason="assign"):
        """Thu mien cua `cell` ve {value}; moi gia tri bi loai duoc ghi vao `log`."""
        for other in sorted(self._sets[cell] - {value}):
            self.remove(cell, other, reason, log)

    def restore(self, removed):
        """Hoan tac cac gia tri da loai (theo thu tu nguoc)."""
        for cell, value, _ in reversed(removed):
            self._sets[cell].add(value)
