"""Doc bang Kakuro tu file JSON. Dung chung cho solver va UI.

Dinh dang o trong JSON:
  "."          o trang (bien)
  "#"          o den
  "d21"        goi y tong cot ben duoi = 21
  "a12"        goi y tong hang ben phai = 12
  "d14/a12"    ca hai goi y

Khoa o dung trong trace va UI co dang chuoi "hang,cot", vi du "2,3".

Moi file trong thu muc puzzles/ deu doc duoc (discover_puzzles / load_all). Bang co
cau truc la la (o chi thuoc 1 run, tong khong the dat...) van duoc nap, kem danh sach
`Puzzle.warnings`; chi bang khong the dua vao CSP moi bi tu choi (ValueError).
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model.kakuro_model import B, W, build_runs, check_model

PUZZLE_DIR = Path(__file__).resolve().parent / "puzzles"


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
    def __init__(self, data, path=None):
        if not isinstance(data, dict) or not data.get("grid"):
            raise ValueError("File puzzle phai la JSON co truong 'grid' khong rong")
        self.data = data
        self.path = Path(path) if path else None
        self.name = data.get("name", "Kakuro")
        self.grid = [list(row) for row in data["grid"]]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        if any(len(row) != self.cols for row in self.grid):
            raise ValueError("Bang khong phai hinh chu nhat")

        # Chuyen sang dang tuple (down, across) cua kakuro_model de dung lai build_runs
        self.model_grid = [[self._parse_token(t) for t in row] for row in self.grid]
        self.model_runs = build_runs(self.model_grid)
        self.warnings = check_model(self.model_grid, self.model_runs)

        self.cells = [f"{r},{c}" for r, row in enumerate(self.grid)
                      for c, t in enumerate(row) if t == W]
        self.runs = [RunInfo(run.name, run.total, tuple(cell_key(c) for c in run.cells))
                     for run in self.model_runs]
        self.run_by_id = {run.id: run for run in self.runs}
        self.peers = {cell: set() for cell in self.cells}
        for run in self.runs:
            for cell in run.cells:
                self.peers[cell].update(x for x in run.cells if x != cell)

    @property
    def label(self):
        """Ten ngan de hien tren nut / bang so sanh, vd 'assignment_9x9' -> '9x9'."""
        stem = self.path.stem if self.path else self.name
        return stem[len("assignment_"):] if stem.startswith("assignment_") else stem

    @staticmethod
    def _parse_token(token):
        if token == "#":
            return B
        if token == ".":
            return W
        down = across = None
        for part in str(token).split("/"):
            if len(part) < 2 or part[0] not in "da" or not part[1:].isdigit():
                raise ValueError(f"Token khong hop le: {token!r}")
            if part[0] == "d":
                down = int(part[1:])
            else:
                across = int(part[1:])
        return (down, across)

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), path)

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


def _natural_key(path):
    """Sap xep theo kich thuoc: 5x5 < 9x9 < 10x10 < 12x12 (khong theo thu tu chu cai)."""
    return [int(n) for n in re.findall(r"\d+", path.stem)], path.stem


def discover_puzzles(directory=None):
    """Danh sach duong dan moi file *.json trong thu muc puzzles, theo thu tu kich thuoc."""
    return sorted(Path(directory or PUZZLE_DIR).glob("*.json"), key=_natural_key)


def load_all(directory=None):
    """Nap moi puzzle trong thu muc. Tra ve (puzzles, errors); errors la [(path, thong bao)].

    Mot file hong khong lam hong ca danh sach: no bi bo qua va ghi vao errors.
    """
    puzzles, errors = [], []
    for path in discover_puzzles(directory):
        try:
            puzzles.append(Puzzle.load(path))
        except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
            errors.append((path, str(exc)))
    return puzzles, errors
