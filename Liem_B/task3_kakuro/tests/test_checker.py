import os
import unittest

from CK_AI_26_27.Liem_B.task3_kakuro.checker import KakuroChecker
from CK_AI_26_27.Liem_B.task3_kakuro.ablation_solver import KakuroCSPSolver
from CK_AI_26_27.Liem_B.task3_kakuro.puzzle_io import load_puzzle

PUZ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "puzzles")

WHITE = [(1, 1), (1, 2), (2, 1), (2, 2)]
CLUES = [(4, [(1, 1), (1, 2)]), (11, [(2, 1), (2, 2)]), (3, [(1, 1), (2, 1)]), (12, [(1, 2), (2, 2)])]


class TestChecker(unittest.TestCase):
    def setUp(self):
        self.ck = KakuroChecker(WHITE, CLUES)

    def test_valid(self):
        self.assertTrue(self.ck.check_solution({(1, 1): 1, (1, 2): 3, (2, 1): 2, (2, 2): 9})[0])

    def test_missing_cell(self):
        self.assertFalse(self.ck.check_solution({(1, 1): 1, (1, 2): 3, (2, 1): 2})[0])

    def test_none_value(self):
        self.assertFalse(self.ck.check_solution({(1, 1): 1, (1, 2): 3, (2, 1): 2, (2, 2): None})[0])

    def test_duplicate_in_run(self):
        self.assertFalse(self.ck.check_solution({(1, 1): 2, (1, 2): 2, (2, 1): 1, (2, 2): 9})[0])

    def test_wrong_sum(self):
        self.assertFalse(self.ck.check_solution({(1, 1): 1, (1, 2): 4, (2, 1): 2, (2, 2): 9})[0])

    def test_out_of_domain(self):
        self.assertFalse(self.ck.check_solution({(1, 1): 0, (1, 2): 4, (2, 1): 3, (2, 2): 8})[0])
        self.assertFalse(self.ck.check_solution({(1, 1): 1, (1, 2): 3, (2, 1): 2, (2, 2): 9.0})[0])


class TestOnAssignmentPuzzles(unittest.TestCase):
    def solve(self, name, **cfg):
        white, clues = load_puzzle(os.path.join(PUZ, name))
        res = KakuroCSPSolver(white, clues, **cfg).solve()
        return KakuroChecker(white, clues), res, white

    def test_5x5_all_configs(self):
        for cfg in [dict(), dict(use_fc=True), dict(use_fc=True, use_prop=True),
                    dict(use_fc=True, use_prop=True, use_heuristics=True)]:
            ck, res, _ = self.solve("assignment_5x5.json", **cfg)
            self.assertTrue(ck.check_solution(res["solution"])[0], cfg)

    def test_9x9_full(self):
        ck, res, _ = self.solve("assignment_9x9.json", use_fc=True, use_prop=True, use_heuristics=True)
        self.assertTrue(ck.check_solution(res["solution"])[0])

    def test_checker_rejects_tampered_9x9(self):
        ck, res, white = self.solve("assignment_9x9.json", use_fc=True, use_prop=True, use_heuristics=True)
        bad = dict(res["solution"])
        a, b = white[0], white[1]
        bad[a], bad[b] = bad[b], bad[a]
        if bad != res["solution"]:
            self.assertFalse(ck.check_solution(bad)[0])


if __name__ == "__main__":
    unittest.main()
