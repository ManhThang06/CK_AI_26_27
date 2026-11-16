"""Tien ich dung chung cho cac bai test."""
from ..model.propagation import Propagator
from ..puzzle import Puzzle, PuzzleRepository

PUZZLES, LOAD_ERRORS = PuzzleRepository().load_all()
BY_LABEL = {p.label: p for p in PUZZLES}
SOLVABLE = [p for p in PUZZLES if not p.warnings]       # bang chuan: 5x5, 9x9

# Bang loi nho tao ngay trong test: run ngang 2 o co tong 30 (khong the dat), run doc chi 1 o.
BROKEN_DATA = {"name": "Broken 2x3",
               "grid": [["#", "d3", "d4"], ["a30", ".", "."]]}
BROKEN = [Puzzle(BROKEN_DATA)]


def count_solutions(puzzle, limit=3):
    """Dem nghiem bang tim kiem doc lap voi cac heuristic cua solver (dung toi da `limit`)."""
    prop = Propagator(puzzle.runs)
    domains = prop.initial_domains()
    ok, _ = prop.propagate_all(domains)
    found = 0

    def search():
        nonlocal found
        free = [c for c, d in domains.items() if len(d) > 1]
        if not free:
            found += 1
            return
        cell = min(free, key=lambda c: (len(domains[c]), c))
        for value in sorted(domains[cell]):
            ok, removed = prop.assign(domains, cell, value)
            if ok:
                search()
            Propagator.undo(domains, removed)
            if found >= limit:
                return

    if ok:
        search()
    return found
