import contextlib
import io
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from .. import __main__ as cli
from .helpers import PUZZLES

try:
    import pygame                                  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class CliTests(unittest.TestCase):
    def test_bench_covers_every_puzzle_and_does_not_crash(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.cmd_bench(Namespace(repeat=1, max_nodes=200000))
        self.assertEqual(code, 0)
        rows = [l for l in out.getvalue().splitlines() if not l.startswith(("puzzle", "  ^"))]
        self.assertEqual(len(rows), len(PUZZLES) * 6)
        for p in PUZZLES:
            self.assertEqual(sum(l.startswith(p.label + " ") for l in rows), 6, p.label)
        self.assertNotIn("Traceback", out.getvalue())

    def test_solve_all_reports_every_puzzle(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.cmd_solve(Namespace(puzzles=[], all=True, variable="mrv-degree",
                                           value="lcv", max_nodes=None))
        text = out.getvalue()
        self.assertEqual(code, 1)                           # co puzzle vo nghiem
        for p in PUZZLES:
            self.assertIn(p.name, text)
        self.assertEqual(text.count("solved, verified=True"), 2)
        self.assertEqual(text.count("unsolvable"), 2)

    def test_solve_single_standard_puzzle_exits_zero(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = cli.cmd_solve(Namespace(puzzles=[PUZZLES[1].path], all=False,
                                           variable="mrv", value="asc", max_nodes=None))
        self.assertEqual(code, 0)


@unittest.skipUnless(HAS_PYGAME, "can pygame de thu giao dien (pip install pygame)")
class UiSmokeTests(unittest.TestCase):
    def test_headless_screenshot_for_every_puzzle(self):
        from ..ui import app
        with tempfile.TemporaryDirectory() as tmp:
            for p in PUZZLES:
                for event in (0, 7, -1):
                    with self.subTest(puzzle=p.label, event=event):
                        out = Path(tmp) / f"{p.label}_{event}.png"
                        app.main(["--headless", "--puzzle", str(p.path), "--screenshot", str(out),
                                  "--event", str(event)])
                        self.assertGreater(out.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
