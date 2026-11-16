"""Puzzle (mot bang Kakuro nhin nhu bai toan CSP) va PuzzleRepository (kho file puzzles/*.json).

Moi file trong thu muc puzzles/ deu doc duoc. Bang co cau truc la (o chi thuoc 1 run, tong
khong the dat...) van duoc nap, kem `Puzzle.warnings`; chi bang khong the dua vao CSP moi bi
tu choi (ValueError).
"""
import json
import re
from pathlib import Path

from .model.board import KakuroBoard

PUZZLE_DIR = Path(__file__).resolve().parent / "puzzles"


class Puzzle:
    def __init__(self, data, path=None):
        if not isinstance(data, dict) or not data.get("grid"):
            raise ValueError("File puzzle phai la JSON co truong 'grid' khong rong")
        self.path = Path(path) if path else None
        self.name = data.get("name", "Kakuro")
        self.board = KakuroBoard(data["grid"])
        self.cells = self.board.cells                  # cac bien (Cell)
        self.runs = self.board.runs                    # cac rang buoc (Run)
        self.warnings = self.board.warnings
        self.run_by_id = {run.name: run for run in self.runs}

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), path)

    @property
    def label(self):
        """Ten ngan de hien tren nut / bang so sanh, vd 'assignment_9x9' -> '9x9'."""
        stem = self.path.stem if self.path else self.name
        return stem[len("assignment_"):] if stem.startswith("assignment_") else stem

    def check(self, assignment):
        """assignment: {"r,c": gia tri}. True neu moi run co tong dung va cac so khac nhau."""
        if set(assignment) != {cell.key for cell in self.cells}:
            return False
        return all(run.is_satisfied_by([assignment[c.key] for c in run.cells])
                   for run in self.runs)


class PuzzleRepository:
    def __init__(self, directory=None):
        self.directory = Path(directory or PUZZLE_DIR)

    @staticmethod
    def _natural_key(path):
        """Sap xep theo kich thuoc: 5x5 < 9x9 < 10x10 < 12x12 (khong theo thu tu chu cai)."""
        return [int(n) for n in re.findall(r"\d+", path.stem)], path.stem

    def paths(self):
        return sorted(self.directory.glob("*.json"), key=self._natural_key)

    def load_all(self):
        """Tra ve (puzzles, errors); errors la [(path, thong bao)]. File hong bi bo qua."""
        puzzles, errors = [], []
        for path in self.paths():
            try:
                puzzles.append(Puzzle.load(path))
            except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
                errors.append((path, str(exc)))
        return puzzles, errors
