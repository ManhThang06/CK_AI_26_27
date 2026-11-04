import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Run:
    id: str
    target: int
    cells: tuple[str, ...]

class Puzzle:
    def __init__(self, data):
        self.name = data.get("name", "Kakuro")
        self.grid = data["grid"]
        if not self.grid or not self.grid[0] or any(len(r) != len(self.grid[0]) for r in self.grid):
            raise ValueError("Puzzle must be rectangular")
        self.rows, self.cols = len(self.grid), len(self.grid[0])
        self.cells = {f"{r},{c}": (r, c) for r in range(self.rows)
                      for c in range(self.cols) if self.grid[r][c] == "."}
        self.runs = []
        coverage = {cell: {"a": 0, "d": 0} for cell in self.cells}
        for r, row in enumerate(self.grid):
            for c, token in enumerate(row):
                if token in ("#", "."):
                    continue
                seen = set()
                for clue in token.split("/"):
                    kind, target = clue[0], int(clue[1:])
                    if kind not in ("a", "d") or kind in seen:
                        raise ValueError("Invalid clue")
                    seen.add(kind)
                    dr, dc = (0, 1) if kind == "a" else (1, 0)
                    rr, cc = r + dr, c + dc
                    cells = []
                    while f"{rr},{cc}" in self.cells:
                        cell = f"{rr},{cc}"
                        cells.append(cell)
                        coverage[cell][kind] += 1
                        rr, cc = rr + dr, cc + dc
                    k = len(cells)
                    if not 2 <= k <= 9 or not k * (k + 1) // 2 <= target <= k * (19 - k) // 2:
                        raise ValueError(f"Invalid run at {r},{c}")
                    self.runs.append(Run(f"{kind}:{r},{c}", target, tuple(cells)))
        if not self.cells or any(x != {"a": 1, "d": 1} for x in coverage.values()):
            raise ValueError("Each white cell must belong to one across and one down run")
        self.peers = {cell: set() for cell in self.cells}
        for run in self.runs:
            for cell in run.cells:
                self.peers[cell].update(set(run.cells) - {cell})

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self):
        return {"name": self.name, "grid": self.grid}

    def check(self, values):
        if set(values) != set(self.cells) or any(type(v) is not int or not 1 <= v <= 9 for v in values.values()):
            return False
        return all(sum(values[c] for c in run.cells) == run.target
                   and len({values[c] for c in run.cells}) == len(run.cells) for run in self.runs)