import random
import unittest

from task1_nqueens.min_conflicts import MinConflictsSolver, Board, slow_conflicts


class TestMinConflicts(unittest.TestCase):
    def test_invalid_board_is_rejected(self):
        for size in (0, -1, True, 4.0):
            with self.subTest(size=size), self.assertRaises(ValueError):
                Board(size)
        for state in ([1, 3, 0], [1, 3, 0, 2, 999], [1, 3, 0, -1], [1, 3, 0, True]):
            with self.subTest(state=state), self.assertRaises(ValueError):
                MinConflictsSolver(4).solve(initial_state=state)

    def test_invalid_solver_configuration_is_rejected(self):
        for config in ({"max_steps": -1}, {"mode": "unknown"}, {"tabu_size": -1},
                       {"restart_after": 0}, {"restart_after": True}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                MinConflictsSolver(4, **config)

    def test_incremental_conflicts_after_moves(self):
        rng = random.Random(12)
        board = Board(20, rng=rng)
        for _ in range(200):
            board.move_queen(rng.randrange(20), rng.randrange(20))
            self.assertEqual(board.total_conflicts(), slow_conflicts(board.state))

    def test_zero_budget_and_last_allowed_move(self):
        solved = MinConflictsSolver(4, max_steps=0).solve(initial_state=[1, 3, 0, 2])
        self.assertTrue(solved["success"])
        self.assertEqual(solved["steps"], 0)
        failed = MinConflictsSolver(4, max_steps=0).solve(initial_state=[0] * 4)
        self.assertFalse(failed["success"])
        solved = MinConflictsSolver(4, max_steps=1).solve(initial_state=[1, 3, 0, 0], seed=0)
        self.assertTrue(solved["success"])
        self.assertEqual(solved["steps"], 1)

    def test_summary_includes_failures_and_custom_variants(self):
        from task1_nqueens.mc_experiment import summarize
        rows = [
            {"N": 8, "variant": "standard", "success": 1, "steps": 10, "time": "0.001"},
            {"N": 8, "variant": "standard", "success": 0, "steps": 100, "time": "0.009"},
        ]
        summary = summarize(rows)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0][2], 50)
        self.assertEqual(summary[0][4], 55)
        self.assertEqual(summary[0][6], 5)

    def test_slow_conflicts_counts_all_pairs(self):
        self.assertEqual(slow_conflicts([0, 1, 2, 3]), 6)
        self.assertEqual(slow_conflicts([1, 3, 0, 2, 2]), 2)
        self.assertEqual(slow_conflicts([1, 3, 0, 2]), 0)

    def test_fast_count_matches_slow(self):
        rng = random.Random(0)
        for n in (4, 8, 13, 30):
            for _ in range(20):
                b = Board(n, rng=rng)
                self.assertEqual(b.total_conflicts(), slow_conflicts(b.state))

    def test_all_modes_give_valid_solution_and_are_reproducible(self):
        for mode in ("standard", "max_tabu", "roulette"):
            a = MinConflictsSolver(20, 20000, mode, 4).solve(seed=3)
            b = MinConflictsSolver(20, 20000, mode, 4).solve(seed=3)
            self.assertTrue(a["success"])
            self.assertEqual(slow_conflicts(a["solution"]), 0)
            self.assertEqual((a["solution"], a["steps"]), (b["solution"], b["steps"]))

    def test_failure_when_out_of_steps(self):
        res = MinConflictsSolver(30, 1, "standard").solve(initial_state=[0] * 30)
        self.assertFalse(res["success"])
        self.assertIsNone(res["solution"])

    def test_restart_escapes_local_minimum(self):
        # Với seed này, bản thuần hết ngân sách còn bản khởi động lại tìm được nghiệm.
        r = random.Random(3); init = [r.randrange(8) for _ in range(8)]
        pure = MinConflictsSolver(8, 20000, "max_tabu", 2).solve(initial_state=init, seed=3)
        rr = MinConflictsSolver(8, 20000, "max_tabu", 2, restart_after=50).solve(initial_state=init, seed=3)
        self.assertFalse(pure["success"])
        self.assertTrue(rr["success"])
        self.assertGreaterEqual(rr["restarts"], 1)
        self.assertEqual(slow_conflicts(rr["solution"]), 0)


if __name__ == "__main__":
    unittest.main()
