"""Backtracking Search ket hop forward checking / loc mien theo run.

Luong chay:
  1. Propagator.propagate_all: node consistency, loc mien tung run mot lan.
  2. Chon bien chua gan bang VariableSelector (MRV, Degree).
  3. Sap xep gia tri bang ValueOrderer (LCV).
  4. Voi moi gia tri: Propagator.assign (forward checking + loc lai hai run chua o do).
     Thanh cong thi de quy, that bai hoac nhanh con that bai thi hoan tac bang danh sach
     (o, gia tri) da xoa roi thu gia tri ke tiep.
"""
import time
from dataclasses import dataclass, field

from ..model.propagation import Propagator
from .heuristics import MRVDegree, LCV
from .trace import Recorder


@dataclass
class SearchStats:
    nodes: int = 0           # so phep gan da thu
    backtracks: int = 0      # so phep gan bi hoan tac
    depth: int = 0           # so phep doan dang nam tren ngan xep
    max_depth: int = 0
    pruned_init: int = 0     # so gia tri bi loai o buoc node consistency


@dataclass
class SolveResult:
    status: str                              # "solved" | "unsolvable" | "limit"
    solution: dict = field(default_factory=dict)   # {"r,c": gia tri}
    verified: bool = False
    stats: SearchStats = field(default_factory=SearchStats)
    seconds: float = 0.0


class BacktrackingSolver:
    def __init__(self, puzzle, variable_selector=None, value_orderer=None,
                 recorder=None, max_nodes=None):
        self.puzzle = puzzle
        self.var_sel = variable_selector or MRVDegree()
        self.val_order = value_orderer or LCV()
        self.max_nodes = max_nodes
        self.stats = SearchStats()
        self.rec = recorder or Recorder()
        self.prop = Propagator(puzzle.model_runs)
        self._limit_hit = False

    @property
    def config(self):
        return {"variable": self.var_sel.name, "value": self.val_order.name,
                "max_nodes": self.max_nodes}

    def solve(self):
        start = time.perf_counter()
        dom = self.prop.initial_domains()
        self.rec.begin(dom)

        ok, removed = self.prop.propagate_all(dom)
        self.stats.pruned_init = len(removed)
        self.rec.removals(dom, removed)

        status = "unsolvable"
        if not ok:
            self.rec.contradiction(dom, self.prop.failed_run)
            self.rec.exhausted(dom)
        elif self._search(dom):
            status = "solved"
            self.rec.solution(dom)
        elif self._limit_hit:
            status = "limit"
            self.rec.limit(dom)
        else:
            self.rec.exhausted(dom)

        result = SolveResult(status, stats=self.stats, seconds=time.perf_counter() - start)
        if status == "solved":
            result.solution = {f"{r},{c}": next(iter(d)) for (r, c), d in dom.items()}
            result.verified = self.puzzle.check(result.solution)
        return result

    def _search(self, domains):
        cell = self.var_sel.select(domains, self.prop)
        if cell is None:                       # moi o da co dung 1 gia tri
            return True
        var_why = self.var_sel.describe(cell, domains, self.prop)
        for value, score in self.val_order.order(cell, domains, self.prop):
            if self.max_nodes is not None and self.stats.nodes >= self.max_nodes:
                self._limit_hit = True
                return False
            self.stats.nodes += 1
            self.stats.depth += 1
            self.stats.max_depth = max(self.stats.max_depth, self.stats.depth)

            ok, removed = self.prop.assign(domains, cell, value)
            message = f"Guess ({cell[0]},{cell[1]}) = {value}. {var_why}"
            val_why = self.val_order.describe(score)
            if val_why:
                message += f"; {val_why}"
            self.rec.removals(domains, removed, message + ".")
            if not ok:
                self.rec.contradiction(domains, self.prop.failed_run)
            elif self._search(domains):
                return True
            if self._limit_hit:
                return False

            Propagator.undo(domains, removed)
            self.stats.backtracks += 1
            self.stats.depth -= 1
            self.rec.backtrack(domains, cell, value, len(removed))
        return False
