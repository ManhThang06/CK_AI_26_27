# Trace of a Kakuro solve, written as a list of events for the UI to replay.
#
# event types (every event also has "step", its position in the list):
#   assign     {"cell": [r, c], "value": v}
#   remove     {"cell": [r, c], "value": v, "reason": "A1"}   value deleted from a domain,
#                                                              reason = run that caused it
#   fail       {"cell": [r, c], "value": v, "reason": "D2"}   the assignment broke run D2
#   backtrack  {"cell": [r, c], "value": v, "restored": [[r, c, v], ...]}
#   solved     {}
import json


class Trace:
    def __init__(self, puzzle_name):
        self.puzzle = puzzle_name
        self.events = []

    def _add(self, event_type, **fields):
        event = {"step": len(self.events), "type": event_type}
        event.update(fields)
        self.events.append(event)

    def assign(self, cell, value):
        self._add("assign", cell=list(cell), value=value)

    def removed(self, removed):
        # removed: list of (cell, value, reason) from Propagator.
        # Entries with reason "assign" are skipped: the assign event already
        # says that the cell's domain became {value}.
        for cell, value, reason in removed:
            if reason != "assign":
                self._add("remove", cell=list(cell), value=value, reason=reason)

    def fail(self, cell, value, reason):
        self._add("fail", cell=list(cell), value=value, reason=reason)

    def backtrack(self, cell, value, removed):
        restored = [[c[0], c[1], v] for c, v, _ in removed]
        self._add("backtrack", cell=list(cell), value=value, restored=restored)

    def solved(self):
        self._add("solved")

    def count(self, event_type):
        return sum(1 for e in self.events if e["type"] == event_type)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"puzzle": self.puzzle, "events": self.events}, f, indent=1)
