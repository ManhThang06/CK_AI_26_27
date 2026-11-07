import json
import os
import tempfile
import unittest

from task3_kakuro.propagation import Propagator
from task3_kakuro.trace import Trace
from task3_kakuro.tools.make_sample_trace import solve
from task3_kakuro.tests.test_propagation import RUNS_5X5, SOLUTION


def make_trace():
    prop = Propagator(RUNS_5X5)
    domains = prop.initial_domains()
    trace = Trace("puzzle_5x5")
    solve(prop, domains, sorted(domains), [], trace)
    return trace


class TestTrace(unittest.TestCase):
    def test_steps_are_consecutive(self):
        trace = make_trace()
        self.assertEqual([e["step"] for e in trace.events], list(range(len(trace.events))))

    def test_assign_reason_is_not_logged_as_remove(self):
        t = Trace("x")
        t.removed([((0, 0), 5, "assign"), ((0, 1), 5, "A1")])
        self.assertEqual(len(t.events), 1)
        self.assertEqual(t.events[0]["reason"], "A1")

    def test_event_types_and_fields(self):
        trace = make_trace()
        need = {"assign": {"cell", "value"}, "remove": {"cell", "value", "reason"},
                "fail": {"cell", "value", "reason"}, "backtrack": {"cell", "value", "restored"}}
        for e in trace.events:
            if e["type"] in need:
                self.assertTrue(need[e["type"]] <= set(e), e)

    def test_sample_has_all_event_kinds_and_ends_solved(self):
        trace = make_trace()
        for kind in ("assign", "remove", "fail", "backtrack"):
            self.assertGreater(trace.count(kind), 0, kind)
        self.assertEqual(trace.events[-1]["type"], "solved")

    def test_fail_reason_is_a_run_name(self):
        names = {r.name for r in RUNS_5X5}
        for e in make_trace().events:
            if e["type"] == "fail":
                self.assertIn(e["reason"], names)

    def test_replay_rebuilds_the_solution(self):
        # what the UI does: apply events one by one to a domain table
        domains = {cell: set(range(1, 10)) for cell in SOLUTION}
        for e in make_trace().events:
            cell = tuple(e.get("cell", ()))
            if e["type"] == "assign":
                domains[cell] = {e["value"]}
            elif e["type"] == "remove":
                domains[cell].discard(e["value"])
            elif e["type"] == "backtrack":
                for r, c, v in e["restored"]:
                    domains[(r, c)].add(v)
        self.assertEqual({c: next(iter(d)) for c, d in domains.items()}, SOLUTION)

    def test_save_and_load_json(self):
        trace = make_trace()
        path = os.path.join(tempfile.mkdtemp(), "t.json")
        trace.save(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["puzzle"], "puzzle_5x5")
        self.assertEqual(data["events"], trace.events)


if __name__ == "__main__":
    unittest.main()
