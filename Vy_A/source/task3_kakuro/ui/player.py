import json
from pathlib import Path
from ..puzzle import Puzzle

class TracePlayer:
    KINDS = {"start", "assign", "propagate", "contradiction", "backtrack", "solution", "exhausted", "limit"}

    def __init__(self, trace):
        if trace.get("schema_version") != 1:
            raise ValueError("Unsupported trace schema")
        self.puzzle = Puzzle(trace["puzzle"])
        self.events = trace["events"]
        if not self.events:
            raise ValueError("Empty trace")
        for event in self.events:
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
        self.reset()

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def reset(self):
        self.index = 0
        self.playing = False
        self.elapsed = 0.0
        self.speed = 4.0

    @property
    def current(self):
        return self.events[self.index]

    def next(self):
        self.index = min(self.index + 1, len(self.events) - 1)
        if self.index == len(self.events) - 1:
            self.playing = False

    def previous(self):
        self.playing = False
        self.index = max(0, self.index - 1)

    def toggle(self):
        if self.index == len(self.events) - 1:
            self.index = 0
        self.playing = not self.playing
        self.elapsed = 0.0

    def tick(self, dt):
        if self.playing:
            self.elapsed += dt
            while self.elapsed >= 1 / self.speed and self.playing:
                self.elapsed -= 1 / self.speed
                self.next()