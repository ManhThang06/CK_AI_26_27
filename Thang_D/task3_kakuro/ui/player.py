"""Theo doi LiveSession: giu vi tri dang xem trong danh sach su kien tang dan.

Solver chay trong thread rieng (solver/live.py) va chi sinh them su kien khi nguoi xem
toi su kien cuoi. Player yeu cau them (demand) va tien len khi su kien do toi.
"""


class LivePlayer:
    KINDS = {"start", "assign", "propagate", "contradiction", "backtrack", "solution", "exhausted", "limit"}

    def __init__(self, session):
        self.session = session
        self.puzzle = session.puzzle
        self.meta = session.meta
        self.events = session.events          # list tang dan, thread solver them vao
        self.checked = 0
        self.sync()
        self.reset()

    def validate(self, event):
        if event.get("kind") not in self.KINDS or set(event.get("domains", {})) != set(self.puzzle.cells):
            raise ValueError("Invalid event or domain keys")
        if event.get("cell") is not None and event["cell"] not in self.puzzle.cells:
            raise ValueError("Invalid highlighted cell")
        for values in event["domains"].values():
            if (not isinstance(values, list) or len(values) != len(set(values))
                    or any(type(v) is not int or not 1 <= v <= 9 for v in values)):
                raise ValueError("Invalid domain")
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
        self.elapsed = 0.0
        self.speed = 4.0

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
        return "Search finished" if self.complete else "Solver advances on demand"

    @property
    def current(self):
        return self.events[self.index]

    def next(self):
        """Tien mot su kien. Neu chua co su kien ke tiep thi yeu cau solver sinh them
        va se tien khi su kien do toi (xem tick)."""
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
        self.index = max(0, self.index - 1)

    def toggle(self):
        if self.at_end:
            self.index = 0
        self.playing = not self.playing
        self.pending = False
        self.elapsed = 0.0

    def tick(self, dt):
        self.sync()
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
