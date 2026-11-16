"""Tao luong su kien tim kiem cho UI.

Moi su kien (TraceEvent) chua anh chup mien cua TAT CA o trang va ngan xep cac phep doan
dang mo (`guesses`), nen UI khong can biet gi ve solver.
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
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TraceEvent:
    kind: str
    cell: Optional[str]                  # khoa "r,c" hoac None
    message: str
    removed: list
    nodes: int
    backtracks: int
    depth: int
    guesses: list                        # [["r,c", gia tri], ...]
    domains: dict                        # {"r,c": [gia tri]}
    run: Optional[str] = None
    value: Optional[int] = None
    restored: Optional[int] = None

    def __getitem__(self, name):
        return getattr(self, name)

    def get(self, name, default=None):
        value = getattr(self, name, None)
        return default if value is None else value


class Recorder:
    """Recorder rong: solver goi cac ham nay nhung khong ghi gi (dung khi benchmark)."""

    def begin(self, domains): pass
    def removals(self, domains, removed, assign_message=None): pass
    def contradiction(self, domains, failed_run): pass
    def backtrack(self, domains, cell, value, restored): pass
    def solution(self, domains): pass
    def exhausted(self, domains): pass
    def limit(self, domains): pass


class TraceRecorder(Recorder):
    TERMINAL = frozenset({"solution", "exhausted", "limit"})

    def __init__(self, puzzle, stats):
        self.puzzle = puzzle
        self.stats = stats            # SearchStats cua solver (nodes, backtracks, depth)
        self.events = []

    # ------------------------------------------------------------ noi bo
    def _emit(self, kind, cell, message, domains, removed=(), **extra):
        self.events.append(TraceEvent(
            kind=kind,
            cell=cell.key if cell else None,
            message=message,
            removed=sorted(removed),
            nodes=self.stats.nodes,
            backtracks=self.stats.backtracks,
            depth=self.stats.depth,
            guesses=[[c.key, v] for c, v in self.stats.stack],
            domains=domains.snapshot(),
            **extra))

    def _run_text(self, run_id):
        return f"{run_id} (sum {self.puzzle.run_by_id[run_id].total})"

    # ------------------------------------------------------------ API cho solver
    def begin(self, domains):
        self._emit("start", None,
                   f"{len(domains)} variables, {len(self.puzzle.runs)} runs. Every domain starts "
                   "as 1..9; node consistency filters each run once.", domains)

    def removals(self, domains, removed, assign_message=None):
        """Chuyen danh sach Removal thanh tung su kien.

        `domains` la trang thai SAU khi xoa. Ta dung lai trang thai TRUOC bang cach them
        gia tri vao lai, roi ap dung tung nhom (cell, reason) de moi su kien co anh chup
        mien dung tai thoi diem do.
        """
        state = domains.copy()
        state.restore(removed)
        i = 0
        while i < len(removed):
            cell, _, reason = removed[i]
            values = []
            while i < len(removed) and removed[i].cell == cell and removed[i].reason == reason:
                values.append(removed[i].value)
                i += 1
            state[cell].difference_update(values)
            if reason == "assign":
                self._emit("assign", cell, assign_message, state, values, value=state.value(cell))
            else:
                self._emit("propagate", cell,
                           f"{self._run_text(reason)} removes {values} from ({cell.row},{cell.col}); "
                           f"domain is now {sorted(state[cell])}.",
                           state, values, run=reason)

    def contradiction(self, domains, failed_run):
        empty = domains.empty_cells()
        if empty:
            cell = empty[0]
            self._emit("contradiction", cell,
                       f"Domain of ({cell.row},{cell.col}) is empty "
                       f"({self._run_text(failed_run)}). Dead end.", domains, run=failed_run)
        else:
            first = self.puzzle.run_by_id[failed_run].cells[0]
            self._emit("contradiction", first,
                       f"{self._run_text(failed_run)} has no valid digit combination left. "
                       "Dead end.", domains, run=failed_run)

    def backtrack(self, domains, cell, value, restored):
        self._emit("backtrack", cell,
                   f"Undo ({cell.row},{cell.col}) = {value}; {restored} removed values restored.",
                   domains, value=value, restored=restored)

    def solution(self, domains):
        self._emit("solution", None,
                   f"Solution found after {self.stats.nodes} nodes and "
                   f"{self.stats.backtracks} backtracks.", domains)

    def exhausted(self, domains):
        self._emit("exhausted", None, "Search space exhausted: this puzzle has no solution.", domains)

    def limit(self, domains):
        self._emit("limit", None, f"Stopped at the limit of {self.stats.nodes} nodes.", domains)
