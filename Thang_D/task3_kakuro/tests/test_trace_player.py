import threading
from dataclasses import replace
import time
import unittest

from ..solver import LiveSession
from ..ui.player import LivePlayer
from .helpers import BY_LABEL, BROKEN, PUZZLES, SOLVABLE


def run_to_end(puzzle, variable="mrv-degree", value="lcv"):
    session = LiveSession(puzzle, variable, value)
    session.start()
    session.finish()
    assert session.wait_finished(), "solver khong ket thuc"
    return session, LivePlayer(session)


class TraceTests(unittest.TestCase):
    def test_event_stream_is_valid_for_every_puzzle(self):
        for p in PUZZLES + BROKEN:
            with self.subTest(p.label):
                session, player = run_to_end(p)
                player.sync()                                 # validate() nem loi neu sai
                self.assertEqual(session.events[0]["kind"], "start")
                self.assertEqual(session.events[-1]["kind"],
                                 "exhausted" if p in BROKEN else "solution")

    def test_guess_stack_follows_the_search(self):
        for p in SOLVABLE:
            for variable, value in (("mrv-degree", "lcv"), ("first", "asc"), ("mrv", "lcv")):
                with self.subTest(puzzle=p.label, variable=variable, value=value):
                    session, _ = run_to_end(p, variable, value)
                    for e in session.events:
                        self.assertEqual(len(e["guesses"]), e["depth"])
                        if e["kind"] == "assign":
                            self.assertEqual(e["guesses"][-1], [e["cell"], e["value"]])
                        if e["kind"] == "backtrack":
                            self.assertNotIn([e["cell"], e["value"]], e["guesses"][-1:])
                    self.assertEqual(session.events[0]["guesses"], [])
                    # tai nghiem: moi phep doan tren ngan xep deu la gia tri cuoi cung cua o do
                    last = session.events[-1]
                    for cell, value in last["guesses"]:
                        self.assertEqual(last["domains"][cell], [value])

    def test_events_are_independent_snapshots(self):
        session, _ = run_to_end(BY_LABEL["9x9"])
        first, last = session.events[0], session.events[-1]
        self.assertTrue(all(len(d) > 1 for d in first["domains"].values()))   # 1..9 ban dau
        self.assertTrue(all(len(d) == 1 for d in last["domains"].values()))


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.session, self.player = run_to_end(BY_LABEL["9x9"], "mrv", "asc")   # co quay lui

    def tearDown(self):
        self.session.stop()

    def test_seek_next_guess_and_backtrack(self):
        p = self.player
        p.seek({"assign"})
        self.assertEqual(p.current["kind"], "assign")
        first = p.index
        p.seek({"assign"})
        self.assertGreater(p.index, first)
        p.reset()
        p.seek({"backtrack"})
        self.assertEqual(p.current["kind"], "backtrack")
        self.assertIsNone(p.seek_kinds)

    def test_seek_without_match_stops_at_the_end(self):
        p = self.player
        p.index = len(p.events) - 1
        p.seek({"assign"})
        self.assertEqual(p.index, len(p.events) - 1)
        self.assertIsNone(p.seek_kinds)

    def test_jump_fraction_and_progress(self):
        p = self.player
        p.jump_fraction(0)
        self.assertEqual((p.index, p.progress), (0, 0.0))
        p.jump_fraction(1)
        self.assertEqual(p.index, len(p.events) - 1)
        self.assertEqual(p.progress, 1.0)
        p.jump_fraction(7)                                   # ngoai khoang -> kep lai
        self.assertEqual(p.index, len(p.events) - 1)

    def test_timeline_marks_every_special_event(self):
        p = self.player
        marks = p.timeline(120)
        self.assertEqual(len(marks), 120)
        kinds = {e["kind"] for e in p.events}
        self.assertTrue({"assign", "backtrack", "solution"} <= kinds)
        # n > width thi cot chon loai quan trong nhat: khong cot nao bi "nuot" mat solution
        self.assertEqual(marks[-1], "solution")
        self.assertIn("backtrack", marks)

    def test_run_details_explain_the_domains(self):
        p = self.player
        p.index = 0
        run = p.puzzle.runs[0]
        d = p.run_details(run)
        self.assertEqual(d["id"], run.name)
        self.assertEqual((d["used"], d["free"], d["rest"]), ([], len(run.cells), run.total))
        # o cuoi: moi run da xong -> khong con o tu do, tong con lai 0
        p.index = len(p.events) - 1
        for run in p.puzzle.runs:
            d = p.run_details(run)
            self.assertEqual((d["free"], d["rest"], d["combos"]), (0, 0, []))

    def test_highlighted_run_matches_event(self):
        p = self.player
        seen = set()
        for i, e in enumerate(p.events):
            p.index = i
            run = p.highlighted_run()
            if e["kind"] in ("propagate", "contradiction"):
                self.assertIsNotNone(run)
                seen.add(e["kind"])
            else:
                self.assertIsNone(run)
        self.assertEqual(seen, {"propagate", "contradiction"})

    def test_summary_only_at_terminal_event(self):
        p = self.player
        p.index = 0
        self.assertIsNone(p.summary())
        p.index = len(p.events) - 1
        s = p.summary()
        self.assertEqual((s["kind"], s["verified"]), ("solution", True))
        self.assertEqual((s["nodes"], s["backtracks"], s["max_depth"]), (28, 17, 11))
        self.assertGreaterEqual(s["ms"], 0)
        self.assertEqual(s["events"], len(p.events))

    def test_summary_for_unsolvable_puzzle(self):
        session, player = run_to_end(BROKEN[0])
        try:
            player.index = len(player.events) - 1
            s = player.summary()
            self.assertEqual((s["kind"], s["verified"]), ("exhausted", False))
        finally:
            session.stop()


class LiveThreadTests(unittest.TestCase):
    def test_solver_advances_only_on_demand(self):
        session = LiveSession(BY_LABEL["9x9"])
        session.start()
        try:
            player = LivePlayer(session)
            self.assertFalse(player.complete)
            player.next()
            player.tick(0)
            self.assertLessEqual(len(session.events), 3)     # khong chay mot mach toi het
            player.seek({"backtrack"})
            deadline = time.monotonic() + 5            # UI tick 60 lan/giay; o day cho toi da 5s
            while player.seek_kinds and time.monotonic() < deadline:
                player.tick(0)
                time.sleep(0.001)
            self.assertEqual(player.current["kind"], "backtrack")
        finally:
            session.stop()

    def test_stop_releases_the_solver_thread(self):
        before = threading.active_count()
        session = LiveSession(BY_LABEL["9x9"])
        session.start()
        session.stop()
        self.assertFalse(session._thread.is_alive())
        self.assertLessEqual(threading.active_count(), before)

    def test_player_rejects_corrupt_events(self):
        session, player = run_to_end(BY_LABEL["5x5"])
        try:
            bad = replace(session.events[1], kind="nonsense")
            with self.assertRaises(ValueError):
                player.validate(bad)
            bad = replace(session.events[1], guesses=[["99,99", 1]])
            with self.assertRaises(ValueError):
                player.validate(bad)
        finally:
            session.stop()


if __name__ == "__main__":
    unittest.main()
