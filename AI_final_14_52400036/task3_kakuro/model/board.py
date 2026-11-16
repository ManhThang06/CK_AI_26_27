from typing import NamedTuple, Optional

from .cell import Cell
from .constraint import Run


class ClueCell(NamedTuple):
    down: Optional[int] = None
    across: Optional[int] = None

    @classmethod
    def parse(cls, token):
        down = across = None
        for part in str(token).split("/"):
            if len(part) < 2 or part[0] not in "da" or not part[1:].isdigit():
                raise ValueError(f"Token khong hop le: {token!r}")
            if part[0] == "d":
                down = int(part[1:])
            else:
                across = int(part[1:])
        return cls(down, across)


class KakuroBoard:
    BLACK = "#"
    WHITE = "."

    def __init__(self, tokens):
        self.tokens = [list(row) for row in tokens]
        self.rows = len(self.tokens)
        self.cols = len(self.tokens[0])
        if any(len(row) != self.cols for row in self.tokens):
            raise ValueError("Bang khong phai hinh chu nhat")
        self._squares = [[self._parse(t) for t in row] for row in self.tokens]
        self.cells = [Cell(r, c) for r in range(self.rows) for c in range(self.cols)
                      if self.is_white(r, c)]
        self.runs = self._build_runs()
        self.warnings = self._check()

    def _parse(self, token):
        if token in (self.BLACK, self.WHITE):
            return token
        return ClueCell.parse(token)

    def is_white(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self._squares[r][c] == self.WHITE

    def clue_at(self, r, c):
        """ClueCell tai (r, c), hoac None neu la o trang / o den khong goi y."""
        square = self._squares[r][c]
        return square if isinstance(square, ClueCell) else None

    def _build_runs(self):
        runs, across_count, down_count = [], 0, 0
        for r in range(self.rows):
            for c in range(self.cols):
                clue = self.clue_at(r, c)
                if clue is None:
                    continue
                if clue.across is not None:
                    across_count += 1
                    cells = self._collect(r, c, 0, 1)
                    runs.append(Run(f"A{across_count}", cells, clue.across))
                if clue.down is not None:
                    down_count += 1
                    cells = self._collect(r, c, 1, 0)
                    runs.append(Run(f"D{down_count}", cells, clue.down))
        return runs

    def _collect(self, r, c, dr, dc):
        cells = []
        r, c = r + dr, c + dc
        while self.is_white(r, c):
            cells.append(Cell(r, c))
            r, c = r + dr, c + dc
        return cells

    def _check(self):
        membership = {}
        for run in self.runs:
            for cell in run.cells:
                membership[cell] = membership.get(cell, 0) + 1
        orphans = sorted(set(self.cells) - set(membership))
        if orphans:
            raise ValueError(f"o trang khong thuoc run nao: {[tuple(c) for c in orphans[:5]]}")

        warnings = []
        single = sorted(c for c, n in membership.items() if n != 2)
        if single:
            warnings.append(f"{len(single)} o trang chi thuoc 1 run, vi du "
                            f"{[tuple(c) for c in single[:3]]}")
        short = [run.name for run in self.runs if run.size < 2]
        if short:
            warnings.append(f"{len(short)} run chi co 1 o: {', '.join(short[:6])}")
        impossible = [f"{run.name}(k={run.size},sum={run.total})"
                      for run in self.runs if not run.is_feasible()]
        if impossible:
            warnings.append(f"{len(impossible)} run co tong khong the dat duoc "
                            f"(vo nghiem): {', '.join(impossible[:6])}")
        return warnings
