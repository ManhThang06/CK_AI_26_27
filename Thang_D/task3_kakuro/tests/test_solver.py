import unittest

from ..solver import BacktrackingSolver, VARIABLE_SELECTORS, VALUE_ORDERERS
from .helpers import BROKEN, BY_LABEL, PUZZLES, SOLVABLE, count_solutions

# (nodes, backtracks, max_depth) cua 9x9 voi tung to hop; trung voi bang trong README.
EXPECTED_9X9 = {
    ("first", "asc"): (9, 2, 7), ("first", "lcv"): (48, 41, 7),
    ("mrv", "asc"): (28, 17, 11), ("mrv", "lcv"): (48, 37, 11),
    ("mrv-degree", "asc"): (12, 3, 9), ("mrv-degree", "lcv"): (18, 9, 9),
}
CONFIGS = [(v, l) for v in VARIABLE_SELECTORS for l in VALUE_ORDERERS]


def solve(puzzle, variable, value, max_nodes=None):
    return BacktrackingSolver(puzzle, VARIABLE_SELECTORS[variable](), VALUE_ORDERERS[value](),
                              max_nodes=max_nodes).solve()


class CorrectnessTests(unittest.TestCase):
    def test_every_config_solves_every_standard_puzzle(self):
        for p in SOLVABLE:
            for variable, value in CONFIGS:
                with self.subTest(puzzle=p.label, variable=variable, value=value):
                    r = solve(p, variable, value)
                    self.assertEqual(r.status, "solved")
                    self.assertTrue(r.verified)
                    self.assertTrue(p.check(r.solution))

    def test_all_configs_agree_on_the_same_solution(self):
        for p in SOLVABLE:
            with self.subTest(p.label):
                solutions = {tuple(sorted(solve(p, v, l).solution.items())) for v, l in CONFIGS}
                self.assertEqual(len(solutions), 1)

    def test_standard_puzzles_have_exactly_one_solution(self):
        for p in SOLVABLE:
            with self.subTest(p.label):
                self.assertEqual(count_solutions(p), 1)

    def test_inconsistent_puzzles_are_reported_unsolvable(self):
        self.assertTrue(BROKEN)
        for p in BROKEN:
            for variable, value in CONFIGS:
                with self.subTest(puzzle=p.label, variable=variable, value=value):
                    r = solve(p, variable, value)
                    self.assertEqual(r.status, "unsolvable")
                    self.assertFalse(r.verified)
                    self.assertEqual(r.solution, {})

    def test_node_limit_stops_the_search(self):
        r = solve(BY_LABEL["9x9"], "first", "lcv", max_nodes=5)
        self.assertEqual(r.status, "limit")
        self.assertLessEqual(r.stats.nodes, 5)
        self.assertFalse(r.verified)


class StabilityTests(unittest.TestCase):
    def test_repeated_runs_give_identical_statistics(self):
        p = BY_LABEL["9x9"]
        for variable, value in CONFIGS:
            with self.subTest(variable=variable, value=value):
                runs = {(r.stats.nodes, r.stats.backtracks, r.stats.max_depth)
                        for r in (solve(p, variable, value) for _ in range(5))}
                self.assertEqual(len(runs), 1)

    def test_search_statistics_match_the_readme_table(self):
        p = BY_LABEL["9x9"]
        for (variable, value), expected in EXPECTED_9X9.items():
            with self.subTest(variable=variable, value=value):
                s = solve(p, variable, value).stats
                self.assertEqual((s.nodes, s.backtracks, s.max_depth), expected)

    def test_stack_is_balanced_after_failed_branches(self):
        # Sau khi tim thay nghiem, ngan xep chinh la cac phep doan tren duong toi nghiem.
        p = BY_LABEL["9x9"]
        r = solve(p, "mrv-degree", "lcv")
        self.assertEqual(len(r.stats.stack), r.stats.depth)
        self.assertEqual(r.stats.nodes - r.stats.backtracks, r.stats.depth)


if __name__ == "__main__":
    unittest.main()
