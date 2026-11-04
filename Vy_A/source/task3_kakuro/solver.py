import argparse
import json
from pathlib import Path
from time import perf_counter
from .puzzle import Puzzle
from .propagation import Propagation

class KakuroSolver:
    def __init__(self, puzzle, heuristics=True, max_nodes=100000):
        self.puzzle = puzzle
        self.heuristics = heuristics
        self.max_nodes = max_nodes
        self.propagation = Propagation(puzzle)

    def emit(self, kind, cell=None, removed=None, message="", depth=0):
        self.events.append({"kind": kind, "cell": cell, "removed": removed or [],
            "message": message, "depth": depth, "nodes": self.nodes, "backtracks": self.backtracks,
            "domains": {c: sorted(values) for c, values in self.domains.items()}})

    def select_variable(self):
        unassigned = [c for c in self.domains if c not in self.assignment]
        if not self.heuristics:
            return unassigned[0]
        return min(unassigned, key=lambda c: (len(self.domains[c]),
            -sum(p not in self.assignment for p in self.puzzle.peers[c]), c))

    def order_values(self, cell):
        values = sorted(self.domains[cell])
        if self.heuristics:
            values.sort(key=lambda v: sum(v in self.domains[p] for p in self.puzzle.peers[cell]
                                         if p not in self.assignment))
        return values

    def backtrack(self, depth=0):
        self.nodes += 1
        if self.nodes > self.max_nodes:
            raise RuntimeError("Search node limit reached")
        if len(self.assignment) == len(self.domains):
            if self.puzzle.check(self.assignment):
                self.emit("solution", message="Verified all runs", depth=depth)
                return dict(self.assignment)
            return None
        cell = self.select_variable()
        for value in self.order_values(cell):
            previous = set(self.domains[cell])
            self.assignment[cell] = value
            self.domains[cell] = {value}
            self.emit("assign", cell, message=f"Try {cell} = {value}", depth=depth+1)
            ok, removed = self.propagation.filter(self.assignment, self.domains, self.emit, depth+1)
            if ok:
                solution = self.backtrack(depth+1)
                if solution is not None:
                    return solution
            else:
                self.emit("contradiction", cell, message="No legal continuation", depth=depth+1)
            self.propagation.restore(self.domains, removed)
            del self.assignment[cell]
            self.domains[cell] = previous
            self.backtracks += 1
            self.emit("backtrack", cell, message="Undo assignment and inferred removals", depth=depth)
        return None

    def solve(self):
        self.assignment = {}
        self.domains = {c: set(range(1, 10)) for c in self.puzzle.cells}
        self.events = []
        self.nodes = self.backtracks = 0
        self.emit("start", message="Initial domains: 1..9")
        start = perf_counter()
        ok, _ = self.propagation.filter(self.assignment, self.domains, self.emit, 0)
        solution = self.backtrack() if ok else None
        if solution is None:
            self.emit("exhausted", message="No solution")
        return {"schema_version": 1, "puzzle": self.puzzle.to_dict(), "events": self.events,
                "result": solution, "nodes": self.nodes, "backtracks": self.backtracks,
                "seconds": perf_counter()-start,
                "configuration": {"heuristics": self.heuristics, "propagation": "combination union, one sweep"}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-heuristics", action="store_true")
    args = parser.parse_args()
    trace = KakuroSolver(Puzzle.load(args.puzzle), heuristics=not args.no_heuristics).solve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(trace), encoding="utf-8")
    print({k: v for k, v in trace.items() if k not in ("events", "puzzle", "result")})