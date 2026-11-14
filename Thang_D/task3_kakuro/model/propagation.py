# Constraint propagation for Kakuro runs (sum + all-different).
# A run is a higher-order constraint, so we filter domains with a table of
# digit combinations instead of the binary AC-3.
from itertools import combinations


def _build_combos():
    table = {}
    for k in range(1, 10):
        for digits in combinations(range(1, 10), k):
            table.setdefault((k, sum(digits)), []).append(frozenset(digits))
    return table


COMBOS = _build_combos()    # (number of cells, sum) -> list of digit sets


def run_state(cells, total, domains):
    """Trang thai cua mot run theo cac mien hien tai (dung chung cho loc mien va UI).

    Tra ve (used, free, rest, combos):
      used    cac chu so cua o da xac dinh (mien 1 gia tri)
      free    cac o chua xac dinh
      rest    tong con lai can dat bang cac o free
      combos  cac tap chu so hop le: dung len(free) chu so khac nhau, tong = rest,
              khong trung used, va nam trong hop mien cua cac o free
    """
    used = [next(iter(domains[c])) for c in cells if len(domains[c]) == 1]
    free = [c for c in cells if len(domains[c]) != 1]
    rest = total - sum(used)
    combos = []
    if free:
        used_set = set(used)
        reachable = set().union(*(domains[c] for c in free))
        combos = [combo for combo in COMBOS.get((len(free), rest), ())
                  if not combo & used_set and combo <= reachable]
    return used, free, rest, combos


class Run:
    def __init__(self, name, cells, total):
        self.name = name              # e.g. "A1" (across) or "D2" (down)
        self.cells = tuple(cells)     # ((row, col), ...)
        self.total = total


class Propagator:
    def __init__(self, runs):
        self.runs = list(runs)
        self.failed_run = None        # name of the run that caused the last failure
        self.runs_of = {}             # cell -> runs that contain it
        for run in self.runs:
            for cell in run.cells:
                self.runs_of.setdefault(cell, []).append(run)

    def initial_domains(self):
        return {cell: set(range(1, 10)) for cell in self.runs_of}

    # ----- public API -------------------------------------------------
    # Every method returns (ok, removed). removed is a list of
    # (cell, value, reason) that were deleted from the domains; on failure
    # it holds the partial deletions, so the caller can still undo them.

    def propagate_all(self, domains):
        # node consistency at the start: filter every run once
        return self._fixpoint(domains, list(self.runs), [])

    def assign(self, domains, cell, value):
        # forward checking: fix cell = value, then filter the runs it touches
        removed = []
        if value not in domains[cell]:
            return False, removed
        for other in sorted(domains[cell] - {value}):
            domains[cell].discard(other)
            removed.append((cell, other, "assign"))
        return self._fixpoint(domains, list(self.runs_of[cell]), removed)

    @staticmethod
    def undo(domains, removed):
        for cell, value, _ in reversed(removed):
            domains[cell].add(value)

    # ----- internals --------------------------------------------------
    def _fixpoint(self, domains, queue, removed):
        queue = list(queue)
        while queue:
            run = queue.pop()
            changed = self._filter_run(run, domains, removed)
            if changed is None:
                self.failed_run = run.name
                return False, removed
            for cell in changed:
                for other in self.runs_of[cell]:
                    if other is not run and other not in queue:
                        queue.append(other)
        return True, removed

    def _filter_run(self, run, domains, removed):
        # returns the cells whose domain shrank, or None if the run is impossible
        used, free, rest, combos = run_state(run.cells, run.total, domains)
        if len(set(used)) < len(used):
            return None                              # two cells share a digit
        if not free:
            return [] if rest == 0 else None
        allowed = set().union(*combos)
        if not allowed:
            return None
        changed = []
        for cell in free:
            for value in sorted(domains[cell] - allowed):
                domains[cell].discard(value)
                removed.append((cell, value, run.name))
                if cell not in changed:
                    changed.append(cell)
            if not domains[cell]:
                return None
        return changed
