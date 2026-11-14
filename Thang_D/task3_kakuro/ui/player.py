"""Theo doi LiveSession: giu vi tri dang xem trong danh sach su kien tang dan.

Solver chay trong thread rieng (solver/live.py) va chi sinh them su kien khi nguoi xem
toi su kien cuoi. Player yeu cau them (demand) va tien len khi su kien do toi.

Moi logic "doc du lieu de ve" (ngan xep phep doan, run dang loc, to hop con hop le,
thanh tien do, tong ket) nam o day de kiem thu duoc ma khong can pygame.
"""
from ..model.propagation import run_state
from ..puzzle import parse_key
from ..solver import BacktrackingSolver, VARIABLE_SELECTORS, VALUE_ORDERERS

TERMINAL = {"solution", "exhausted", "limit"}
# Do uu tien khi nhieu su kien roi vao cung mot cot cua thanh tien do
_PRIORITY = {"start": 0, "propagate": 1, "assign": 2, "backtrack": 3,
             "contradiction": 4, "solution": 5, "exhausted": 5, "limit": 5}


class LivePlayer:
    KINDS = set(_PRIORITY)
    SEEK_BATCH = 200          # so su kien yeu cau them moi lan khi dang tim "next guess/backtrack"

    def __init__(self, session):
        self.session = session
        self.puzzle = session.puzzle
        self.meta = session.meta
        self.events = session.events          # list tang dan, thread solver them vao
        self.checked = 0
        self._timeline = (None, None)         # (khoa cache, ket qua)
        self._solo_ms = None
        self._summary = (None, None)          # (khoa cache, ket qua)
        self.sync()
        self.reset()

    # ------------------------------------------------------------ kiem tra su kien
    def validate(self, event):
        cells = set(self.puzzle.cells)
        if event.get("kind") not in self.KINDS or set(event.get("domains", {})) != cells:
            raise ValueError("Invalid event or domain keys")
        if event.get("cell") is not None and event["cell"] not in cells:
            raise ValueError("Invalid highlighted cell")
        if event.get("run") is not None and event["run"] not in self.puzzle.run_by_id:
            raise ValueError("Invalid run")
        for values in event["domains"].values():
            if (not isinstance(values, list) or len(values) != len(set(values))
                    or any(type(v) is not int or not 1 <= v <= 9 for v in values)):
                raise ValueError("Invalid domain")
        guesses = event.get("guesses")
        if not isinstance(guesses, list) or any(
                len(g) != 2 or g[0] not in cells or type(g[1]) is not int for g in guesses):
            raise ValueError("Invalid guess stack")
        if event["kind"] == "solution":
            if any(len(d) != 1 for d in event["domains"].values()) or not self.puzzle.check(
                    {c: d[0] for c, d in event["domains"].items()}):
                raise ValueError("Invalid solution event")

    def sync(self):
        """Kiem tra cac su kien moi den."""
        end = len(self.events)
        for event in self.events[self.checked:end]:
            self.validate(event)
        self.checked = end

    def reset(self):
        self.index = 0
        self.playing = False
        self.pending = False
        self.seek_kinds = None
        self.elapsed = 0.0
        self.speed = 4.0

    # ------------------------------------------------------------ trang thai
    @property
    def complete(self):
        """True khi solver da sinh su kien cuoi (hoac bi loi)."""
        return self.session.finished

    @property
    def at_end(self):
        return self.index == len(self.events) - 1 and self.complete

    @property
    def total_text(self):
        return f"{len(self.events):03d}" + ("" if self.complete else "+")

    @property
    def status_text(self):
        if self.session.error:
            return f"Solver error: {self.session.error}"
        if self.complete:
            return "Search finished"
        if self.seek_kinds:
            return "Seeking..."
        return "Playing" if self.playing else "Paused (solver waits)"

    @property
    def current(self):
        return self.events[self.index]

    # ------------------------------------------------------------ dieu khien
    def next(self):
        """Tien mot su kien. Neu chua co su kien ke tiep thi yeu cau solver sinh them
        va se tien khi su kien do toi (xem tick)."""
        self.seek_kinds = None
        self.sync()
        if self.index < len(self.events) - 1:
            self.index += 1
            self.pending = False
        elif not self.complete:
            self.pending = True
            self.session.demand(len(self.events) + 1)
        if self.at_end:
            self.playing = False

    def previous(self):
        self.playing = False
        self.pending = False
        self.seek_kinds = None
        self.index = max(0, self.index - 1)

    def toggle(self):
        self.seek_kinds = None
        if self.at_end:
            self.index = 0
        self.playing = not self.playing
        self.pending = False
        self.elapsed = 0.0

    def jump_fraction(self, fraction):
        """Nhay toi vi tri `fraction` (0..1) trong cac su kien da sinh (thanh tien do)."""
        self.playing = False
        self.pending = False
        self.seek_kinds = None
        last = len(self.events) - 1
        self.index = max(0, min(last, round(fraction * last)))

    def seek(self, kinds):
        """Nhay toi su kien ke tiep thuoc `kinds` (vd {"assign"}); cho solver sinh them neu can."""
        self.playing = False
        self.pending = False
        self.seek_kinds = set(kinds)
        self._advance_seek()

    def _advance_seek(self):
        if not self.seek_kinds:
            return
        self.sync()
        done = self.complete              # doc TRUOC khi quet: done=True thi khong con su kien moi
        for i in range(self.index + 1, len(self.events)):
            if self.events[i]["kind"] in self.seek_kinds:
                self.index = i
                self.seek_kinds = None
                return
        self.index = len(self.events) - 1  # chua thay: dung o cuoi phan da sinh
        if done:
            self.seek_kinds = None
        else:
            self.session.demand(len(self.events) + self.SEEK_BATCH)

    def tick(self, dt):
        self.sync()
        self._advance_seek()
        if self.pending and self.index < len(self.events) - 1:
            self.index += 1
            self.pending = False
            if self.at_end:
                self.playing = False
        if self.playing:
            self.elapsed += dt
            while self.elapsed >= 1 / self.speed and self.playing:
                self.elapsed -= 1 / self.speed
                self.next()

    # ------------------------------------------------------------ du lieu de ve
    def guess_cells(self, event=None):
        """{"r,c": gia tri} cua cac o dang la phep doan (ngan xep tai su kien nay)."""
        return {cell: value for cell, value in (event or self.current)["guesses"]}

    def highlighted_run(self, event=None):
        """RunInfo ma su kien (propagate / contradiction) dang noi toi, hoac None."""
        run_id = (event or self.current).get("run")
        return self.puzzle.run_by_id.get(run_id) if run_id else None

    def run_details(self, run, event=None):
        """Mot run xet theo mien tai su kien: chu so da co, tong con lai, cac to hop con hop le."""
        event = event or self.current
        domains = {parse_key(c): set(event["domains"][c]) for c in run.cells}
        used, free, rest, combos = run_state([parse_key(c) for c in run.cells], run.target, domains)
        return {"id": run.id, "target": run.target, "size": len(run.cells),
                "used": sorted(used), "free": len(free), "rest": rest,
                "combos": sorted(sorted(c) for c in combos)}

    @property
    def progress(self):
        """Vi tri hien tai tren thanh tien do, 0..1."""
        last = len(self.events) - 1
        return self.index / last if last > 0 else 0.0

    def timeline(self, width):
        """Mot phan tu moi cot pixel: loai su kien noi bat nhat roi vao cot do (hoac None)."""
        key = (len(self.events), width)
        if self._timeline[0] == key:
            return self._timeline[1]
        n = len(self.events)
        marks = [None] * max(0, width)
        for i in range(n):
            x = min(width - 1, i * width // n)
            kind = self.events[i]["kind"]
            if marks[x] is None or _PRIORITY[kind] > _PRIORITY[marks[x]]:
                marks[x] = kind
        self._timeline = (key, marks)
        return marks

    def summary(self):
        """Tong ket khi dang xem su kien cuoi (solution / exhausted / limit); nguoc lai None."""
        event = self.current
        if event["kind"] not in TERMINAL:
            return None
        key = (self.index, len(self.events))
        if self._summary[0] == key:
            return self._summary[1]
        if self._solo_ms is None:
            self._solo_ms = self._solo_time_ms()
        result = {"kind": event["kind"],
                  "verified": event["kind"] == "solution",   # validate() da goi Puzzle.check
                  "nodes": event["nodes"], "backtracks": event["backtracks"],
                  "max_depth": max(e["depth"] for e in self.events[:self.index + 1]),
                  "events": len(self.events), "ms": self._solo_ms}
        self._summary = (key, result)
        return result

    def _solo_time_ms(self):
        """Thoi gian giai thuan (khong co UI, khong ghi trace). Thoi gian trong luc UI chay
        khong dung duoc vi thread solver phai cho nguoi xem."""
        solver = BacktrackingSolver(self.puzzle, VARIABLE_SELECTORS[self.meta["variable"]](),
                                    VALUE_ORDERERS[self.meta["value"]](),
                                    max_nodes=self.meta.get("max_nodes"))
        return solver.solve().seconds * 1000
