"""Tao luong su kien tim kiem cho UI.

Moi su kien chua anh chup mien cua TAT CA o trang, nen UI khong can biet gi ve solver.
Cac loai su kien (kind):
  start          mien ban dau 1..9
  propagate      mot run loc bot gia tri khoi mien mot o (cell, removed, run)
  assign         doan cell = value (buoc re nhanh cua Backtracking)
  contradiction  mot mien rong hoac mot run khong con to hop hop le
  backtrack      hoan tac phep gan, mien duoc khoi phuc
  solution       tim thay nghiem
  exhausted      da thu het ma khong co nghiem
  limit          dung do cham gioi han so nut
"""
from ..puzzle import cell_key


class Recorder:
    """Recorder rong: solver goi cac ham nay nhung khong ghi gi (dung khi benchmark)."""
    enabled = False

    def begin(self, domains): pass
    def removals(self, domains, removed, assign_message=None): pass
    def contradiction(self, domains, failed_run): pass
    def backtrack(self, domains, cell, value, restored): pass
    def solution(self, domains): pass
    def exhausted(self, domains): pass
    def limit(self, domains): pass


class TraceRecorder(Recorder):
    enabled = True

    def __init__(self, puzzle, stats):
        self.puzzle = puzzle
        self.stats = stats            # SearchStats cua solver (nodes, backtracks, depth)
        self.events = []

    # ------------------------------------------------------------ noi bo
    def _emit(self, kind, cell, message, domains, removed=(), **extra):
        event = {
            "kind": kind,
            "cell": cell_key(cell) if cell else None,
            "message": message,
            "removed": sorted(removed),
            "nodes": self.stats.nodes,
            "backtracks": self.stats.backtracks,
            "depth": self.stats.depth,
            "domains": {cell_key(c): sorted(domains[c]) for c in sorted(domains)},
        }
        event.update(extra)
        self.events.append(event)

    def _run_text(self, run_id):
        return f"{run_id} (sum {self.puzzle.run_by_id[run_id].target})"

    # ------------------------------------------------------------ API cho solver
    def begin(self, domains):
        n = len(domains)
        self._emit("start", None,
                   f"{n} variables, {len(self.puzzle.runs)} runs. Every domain starts as 1..9; "
                   "node consistency filters each run once.", domains)

    def removals(self, domains, removed, assign_message=None):
        """Chuyen danh sach `removed` (cell, value, reason) thanh tung su kien.

        `domains` la trang thai SAU khi xoa. Ta dung lai trang thai TRUOC bang cach
        them gia tri vao lai, roi ap dung tung nhom (cell, reason) de moi su kien
        co anh chup mien dung tai thoi diem do.
        """
        state = {c: set(d) for c, d in domains.items()}
        for cell, value, _ in removed:
            state[cell].add(value)
        i = 0
        while i < len(removed):
            cell, _, reason = removed[i]
            values = []
            while i < len(removed) and removed[i][0] == cell and removed[i][2] == reason:
                values.append(removed[i][1])
                i += 1
            state[cell].difference_update(values)
            if reason == "assign":
                self._emit("assign", cell, assign_message, state, values,
                           value=next(iter(state[cell])))
            else:
                text = self._run_text(reason)
                self._emit("propagate", cell,
                           f"{text} removes {values} from ({cell[0]},{cell[1]}); "
                           f"domain is now {sorted(state[cell])}.",
                           state, values, run=reason)

    def contradiction(self, domains, failed_run):
        empty = sorted(c for c, d in domains.items() if not d)
        if empty:
            r, c = empty[0]
            self._emit("contradiction", empty[0],
                       f"Domain of ({r},{c}) is empty ({self._run_text(failed_run)}). Dead end.",
                       domains, run=failed_run)
        else:
            first = self.puzzle.run_by_id[failed_run].cells[0]
            r, c = first.split(",")
            self._emit("contradiction", (int(r), int(c)),
                       f"{self._run_text(failed_run)} has no valid digit combination left. Dead end.",
                       domains, run=failed_run)

    def backtrack(self, domains, cell, value, restored):
        self._emit("backtrack", cell,
                   f"Undo ({cell[0]},{cell[1]}) = {value}; {restored} removed values restored.",
                   domains, value=value, restored=restored)

    def solution(self, domains):
        self._emit("solution", None,
                   f"Solution found after {self.stats.nodes} nodes and "
                   f"{self.stats.backtracks} backtracks.", domains)

    def exhausted(self, domains):
        self._emit("exhausted", None, "Search space exhausted: this puzzle has no solution.", domains)

    def limit(self, domains):
        self._emit("limit", None, f"Stopped at the limit of {self.stats.nodes} nodes.", domains)
