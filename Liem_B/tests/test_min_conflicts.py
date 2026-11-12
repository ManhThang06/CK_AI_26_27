import random
import unittest

from CK_AI_26_27.Liem_B.task1_nqueens.min_conflicts import MinConflictsSolver, Board, slow_conflicts


class TestMinConflicts(unittest.TestCase):
    def test_slow_conflicts_counts_all_pairs(self):
        self.assertEqual(slow_conflicts([0, 1, 2, 3]), 6)       # ban cu tra 3
        self.assertEqual(slow_conflicts([1, 3, 0, 2, 2]), 2)    # ban cu tra 0
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
        # seed 3, N=8, max_tabu: ban thuan ket o h=1 (that bai); co restart thi giai duoc
        import random
        r = random.Random(3); init = [r.randrange(8) for _ in range(8)]
        pure = MinConflictsSolver(8, 20000, "max_tabu", 2).solve(initial_state=init, seed=3)
        rr = MinConflictsSolver(8, 20000, "max_tabu", 2, restart_after=50).solve(initial_state=init, seed=3)
        self.assertFalse(pure["success"])
        self.assertTrue(rr["success"])
        self.assertGreaterEqual(rr["restarts"], 1)
        self.assertEqual(slow_conflicts(rr["solution"]), 0)


if __name__ == "__main__":
    unittest.main()
