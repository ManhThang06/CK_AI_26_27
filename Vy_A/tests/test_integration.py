import copy
import itertools
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from task1_nqueens.cnf_encoder import CNFEncoder
from task1_nqueens.sat_solver import SATSolver
from task1_nqueens.board import Board
from task1_nqueens.analysis import load_csv, require_columns
from task2_tank.engine import GameMap, GameState, Action
from task3_kakuro.puzzle import Puzzle
from task3_kakuro.solver import KakuroSolver
from task3_kakuro.propagation import Propagation
from task3_kakuro.ui.player import TracePlayer

K = ROOT / "source/task3_kakuro"

class IntegrationTests(unittest.TestCase):
    def test_sat_models_and_counts(self):
        for n in range(1, 13):
            encoder = CNFEncoder(n)
            clauses = encoder.encode()
            self.assertEqual(len(clauses), n+n*n*(n-1)+n*(n-1)*(2*n-1)//3)
            result = SATSolver().solve(n)
            self.assertEqual(result["sat"], n not in (2, 3))
            if result["sat"]:
                self.assertTrue(Board(result["columns"]).is_valid())

    def test_all_4queen_permutations_match_cnf(self):
        encoder = CNFEncoder(4)
        for columns in itertools.permutations(range(4)):
            true = {encoder.variable(r,c) for r,c in enumerate(columns)}
            valid = all(any(v in true if v > 0 else -v not in true for v in clause)
                        for clause in encoder.encode())
            self.assertEqual(valid, Board(columns).is_valid())

    def test_real_csv_matches_c_analysis(self):
        rows = load_csv(ROOT / "source/task1_nqueens/data/measured/sat.csv")
        require_columns(rows, ["N", "num_clauses", "gen_time", "solve_time"], "measured")
        self.assertEqual(len(rows), 45)

    def test_team_maps(self):
        for path in (ROOT / "source/task2_tank/maps").glob("*.txt"):
            state = GameState.from_map(GameMap.load(path))
            self.assertEqual(len(state.tanks), 2)
            changed = state.result(Action.STAY).result(Action.STAY)
            self.assertEqual(changed.cycle, 1)
            self.assertEqual(state.cycle, 0)

    def test_propagation_never_removes_legal_small_run_values(self):
        class Tiny:
            pass
        class Run:
            cells = ("a", "b", "c")
            target = 7
            id = "test"
        p = Tiny()
        p.runs = [Run()]
        for choices in [({1,2,3,4}, {1,2,4}, {1,2,3,4}), ({1}, {1}, {5}), ({1,2}, {2,4}, {1,4})]:
            domains = dict(zip(Run.cells, map(set, choices)))
            before = copy.deepcopy(domains)
            assignment = {}
            legal = [t for t in itertools.product(*(before[c] for c in Run.cells))
                     if len(set(t)) == 3 and sum(t) == 7]
            ok, removed = Propagation(p).filter(assignment, domains, lambda *args: None, 0)
            if legal:
                self.assertTrue(ok)
                for values in legal:
                    self.assertTrue(all(v in domains[c] for c,v in zip(Run.cells, values)))
            Propagation.restore(domains, removed)
            self.assertEqual(domains, before)

    def test_puzzles_and_backtrack_restoration(self):
        for size in (5, 9):
            puzzle = Puzzle.load(K / f"puzzles/assignment_{size}x{size}.json")
            trace = KakuroSolver(puzzle).solve()
            self.assertTrue(puzzle.check(trace["result"]))
            TracePlayer(trace)
            previous = trace["events"][0]
            stack = []
            for event in trace["events"][1:]:
                if event["kind"] == "assign":
                    stack.append(copy.deepcopy(previous["domains"]))
                elif event["kind"] == "backtrack":
                    self.assertEqual(event["domains"], stack.pop())
                previous = event
            if size == 9:
                self.assertGreater(trace["backtracks"], 0)

    def test_unsat_returns_failure(self):
        puzzle = Puzzle.load(K / "puzzles/assignment_5x5.json")
        data = puzzle.to_dict()
        data["grid"] = copy.deepcopy(data["grid"])
        data["grid"][1][1] = "d14/a13"
        trace = KakuroSolver(Puzzle(data)).solve()
        self.assertIsNone(trace["result"])
        self.assertEqual(trace["events"][-1]["kind"], "exhausted")

    def test_ui_new_trace_and_replay(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        from task3_kakuro.ui.app import KakuroApp
        app = KakuroApp(K / "traces/assignment_9x9.json")
        try:
            for kind in ("start", "assign", "propagate", "contradiction", "backtrack", "solution"):
                app.player.index = next(i for i,e in enumerate(app.player.events) if e["kind"] == kind)
                app.draw()
            app.player.reset()
            app.player.toggle()
            app.player.tick(1)
            self.assertEqual(app.player.index, 4)
            app.player.previous()
            self.assertEqual(app.player.index, 3)
        finally:
            app.pg.quit()

if __name__ == "__main__":
    unittest.main()