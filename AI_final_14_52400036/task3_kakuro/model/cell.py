"""Cell: toa do mot o trang (bien cua CSP). La NamedTuple nen so sanh/sap xep nhu tuple (r, c)."""
from typing import NamedTuple


class Cell(NamedTuple):
    row: int
    col: int

    @property
    def key(self):
        """Khoa chuoi "hang,cot" dung trong su kien trace va UI."""
        return f"{self.row},{self.col}"

    @classmethod
    def parse(cls, key):
        row, col = key.split(",")
        return cls(int(row), int(col))
