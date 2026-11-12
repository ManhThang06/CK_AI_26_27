"""Doc bang Kakuro tu file JSON. Dung chung cho solver va UI.

Dinh dang o trong JSON:
  "."          o trang (bien)
  "#"          o den
  "d21"        goi y tong cot ben duoi = 21
  "a12"        goi y tong hang ben phai = 12
  "d14/a12"    ca hai goi y

Khoa o dung trong trace va UI co dang chuoi "hang,cot", vi du "2,3".
"""
import json
from dataclasses import dataclass
from pathlib import Path

from .model.kakuro_model import B, W, build_runs, check_model


def cell_key(cell):
    """(r, c) -> "r,c"."""
    return f"{cell[0]},{cell[1]}"


def parse_key(key):
    """"r,c" -> (r, c)."""
    r, c = key.split(",")
    return int(r), int(c)


@dataclass(frozen=True)
class RunInfo:
    id: str          # "A1" (ngang) hoac "D2" (doc)
    target: int      # tong goi y
    cells: tuple     # cac khoa "r,c" theo thu tu


class Puzzle:
    def __init__(self, data):
        self.data = data
        self.name = data.get("name", "Kakuro")
        self.grid = [list(row) for row in data["grid"]]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        if any(len(row) != self.cols for row in self.grid):
            raise ValueError("Bang khong phai hinh chu nhat")

        # Chuyen sang dang tuple (down, across) cua kakuro_model de dung lai build_runs
        self.model_grid = [[self._parse_token(t) for t in row] for row in self.grid]
        self.model_runs = build_runs(self.model_grid)
        check_model(self.model_grid, self.model_runs)

        self.cells = [f"{r},{c}" for r, row in enumerate(self.grid)
                      for c, t in enumerate(row) if t == W]
        self.runs = [RunInfo(run.name, run.total, tuple(cell_key(c) for c in run.cells))
                     for run in self.model_runs]
        self.run_by_id = {run.id: run for run in self.runs}
        self.peers = {cell: set() for cell in self.cells}
        for run in self.runs:
            for cell in run.cells:
                self.peers[cell].update(x for x in run.cells if x != cell)

    @staticmethod
    def _parse_token(token):
        if token == "#":
            return B
        if token == ".":
            return W
        down = across = None
        for part in token.split("/"):
            if len(part) < 2 or part[0] not in "da" or not part[1:].isdigit():
                raise ValueError(f"Token khong hop le: {token!r}")
            if part[0] == "d":
                down = int(part[1:])
            else:
                across = int(part[1:])
        return (down, across)

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def check(self, assignment):
        """assignment: {"r,c": gia tri}. True neu moi run co tong dung va cac so khac nhau."""
        if set(assignment) != set(self.cells):
            return False
        for run in self.runs:
            values = [assignment[c] for c in run.cells]
            if any(type(v) is not int or not 1 <= v <= 9 for v in values):
                return False
            if len(set(values)) != len(values) or sum(values) != run.target:
                return False
        return True
