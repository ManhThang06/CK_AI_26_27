import copy
import unittest

from task3_kakuro.propagation import COMBOS, Run, Propagator

# 5x5 board from the assignment. Cells are (row, col).
RUNS_5X5 = [
    Run("A1", [(1, 2), (1, 3)], 12),
    Run("A2", [(2, 1), (2, 2), (2, 3), (2, 4)], 21),
    Run("A3", [(3, 1), (3, 2), (3, 3), (3, 4)], 11),
    Run("A4", [(4, 2), (4, 3)], 16),
    Run("D1", [(1, 2), (2, 2), (3, 2), (4, 2)], 21),
    Run("D2", [(1, 3), (2, 3), (3, 3), (4, 3)], 14),
    Run("D3", [(2, 1), (3, 1)], 14),
    Run("D4", [(2, 4), (3, 4)], 11),
]

SOLUTION = {(1, 2): 8, (1, 3): 4,
            (2, 1): 9, (2, 2): 3, (2, 3): 1, (2, 4): 8,
            (3, 1): 5, (3, 2): 1, (3, 3): 2, (3, 4): 3,
            (4, 2): 9, (4, 3): 7}


class TestCombos(unittest.TestCase):
    def test_known_entries(self):
        self.assertEqual(COMBOS[(2, 3)], [frozenset({1, 2})])
        self.assertEqual(COMBOS[(2, 17)], [frozenset({8, 9})])
        self.assertEqual(len(COMBOS[(2, 10)]), 4)

    def test_every_combo_is_valid(self):
        for (k, total), combos in COMBOS.items():
            for combo in combos:
                self.assertEqual(len(combo), k)
                self.assertEqual(sum(combo), total)


class TestPropagation5x5(unittest.TestCase):
    def setUp(self):
        self.prop = Propagator(RUNS_5X5)
        self.domains = self.prop.initial_domains()

    def test_twelve_variables(self):
        self.assertEqual(len(self.domains), 12)

    def test_initial_propagation_matches_hand_calculation(self):
        ok, _ = self.prop.propagate_all(self.domains)
        self.assertTrue(ok)
        # run A4 (two cells, sum 16) can only be {7, 9}
        # run D3 (two cells, sum 14) forces (2,1)=9 after the other runs agree
        solved = {cell: next(iter(d)) for cell, d in self.domains.items()}
        self.assertEqual(solved, SOLUTION)

    def test_never_removes_a_value_of_the_solution(self):
        self.prop.propagate_all(self.domains)
        for cell, value in SOLUTION.items():
            self.assertIn(value, self.domains[cell])

    def test_removed_list_records_cause(self):
        _, removed = self.prop.propagate_all(self.domains)
        self.assertTrue(removed)
        names = {run.name for run in RUNS_5X5} | {"assign"}
        for cell, value, reason in removed:
            self.assertIn(reason, names)

    def test_undo_restores_domains(self):
        before = copy.deepcopy(self.domains)
        _, removed = self.prop.propagate_all(self.domains)
        self.prop.undo(self.domains, removed)
        self.assertEqual(self.domains, before)

    def test_assign_wrong_value_fails_and_can_be_undone(self):
        before = copy.deepcopy(self.domains)
        ok, removed = self.prop.assign(self.domains, (4, 2), 8)   # A4 needs 7 or 9
        self.assertFalse(ok)
        self.prop.undo(self.domains, removed)
        self.assertEqual(self.domains, before)

    def test_assign_right_value_is_kept(self):
        ok, _ = self.prop.assign(self.domains, (4, 2), 9)
        self.assertTrue(ok)
        self.assertEqual(self.domains[(4, 3)], {7})

    def test_assign_value_not_in_domain(self):
        self.domains[(1, 2)].discard(5)
        ok, removed = self.prop.assign(self.domains, (1, 2), 5)
        self.assertFalse(ok)
        self.assertEqual(removed, [])


class TestSmallRun(unittest.TestCase):
    def test_three_cells_sum_7(self):
        cells = [(0, 0), (0, 1), (0, 2)]
        prop = Propagator([Run("A1", cells, 7)])
        d = prop.initial_domains()
        self.assertTrue(prop.propagate_all(d)[0])
        for c in cells:
            self.assertEqual(d[c], {1, 2, 4})
        ok, _ = prop.assign(d, (0, 0), 4)
        self.assertTrue(ok)
        self.assertEqual(d[(0, 1)], {1, 2})
        self.assertEqual(d[(0, 2)], {1, 2})

    def test_impossible_sum(self):
        prop = Propagator([Run("A1", [(0, 0), (0, 1)], 2)])    # 1+1 needs a repeat
        ok, _ = prop.propagate_all(prop.initial_domains())
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
