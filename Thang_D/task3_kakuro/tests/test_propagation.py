import unittest

from ..model.propagation import COMBOS, Propagator, run_state
from ..solver import BacktrackingSolver
from .helpers import BY_LABEL, SOLVABLE


class CombosTests(unittest.TestCase):
    def test_known_combinations(self):
        self.assertEqual(COMBOS[(2, 3)], [frozenset({1, 2})])
        self.assertEqual(COMBOS[(3, 6)], [frozenset({1, 2, 3})])
        self.assertEqual(COMBOS[(9, 45)], [frozenset(range(1, 10))])
        self.assertNotIn((2, 2), COMBOS)                  # 2 chu so khac nhau khong the co tong 2

    def test_run_state(self):
        domains = {(0, 0): {7}, (0, 1): {1, 2, 3, 4, 5, 6, 7, 8, 9}, (0, 2): {1, 2, 3, 4, 5}}
        used, free, rest, combos = run_state([(0, 0), (0, 1), (0, 2)], 12, domains)
        self.assertEqual((used, rest, len(free)), ([7], 5, 2))
        self.assertEqual(sorted(sorted(c) for c in combos), [[1, 4], [2, 3]])


class PropagatorTests(unittest.TestCase):
    def test_propagation_is_sound(self):
        """Loc mien chi bo gia tri khong the dung: nghiem duy nhat luon con trong mien,
        ap dung lai nhieu lan chi thu hep them va khong bao gio lam rong mien.

        (Luu y: propagate_all khong lap toi diem co dinh tuyet doi; lan goi thu hai co the
        loai them gia tri. Do la dieu kien yeu hon, khong anh huong tinh dung.)
        """
        for p in SOLVABLE:
            with self.subTest(p.label):
                solution = BacktrackingSolver(p).solve().solution
                prop = Propagator(p.model_runs)
                domains = prop.initial_domains()
                previous = {c: set(d) for c, d in domains.items()}
                for _ in range(4):
                    ok, _ = prop.propagate_all(domains)
                    self.assertTrue(ok)
                    for (r, c), d in domains.items():
                        self.assertIn(solution[f"{r},{c}"], d)
                        self.assertLessEqual(d, previous[(r, c)])
                    previous = {c: set(d) for c, d in domains.items()}

    def test_assign_then_undo_restores_domains_exactly(self):
        p = BY_LABEL["9x9"]
        prop = Propagator(p.model_runs)
        domains = prop.initial_domains()
        prop.propagate_all(domains)
        before = {c: set(d) for c, d in domains.items()}
        for cell in [c for c, d in domains.items() if len(d) > 1][:12]:
            for value in sorted(domains[cell]):
                ok, removed = prop.assign(domains, cell, value)
                Propagator.undo(domains, removed)
                self.assertEqual(domains, before, f"{cell}={value} ok={ok}")

    def test_assign_value_outside_domain_fails(self):
        p = BY_LABEL["9x9"]
        prop = Propagator(p.model_runs)
        domains = prop.initial_domains()
        prop.propagate_all(domains)
        cell = next(c for c, d in domains.items() if len(d) > 1 and 9 not in d)
        ok, removed = prop.assign(domains, cell, 9)
        self.assertFalse(ok)
        self.assertEqual(removed, [])

    def test_impossible_run_makes_propagate_all_fail(self):
        for label in ("10x10", "12x12"):
            with self.subTest(label):
                prop = Propagator(BY_LABEL[label].model_runs)
                ok, _ = prop.propagate_all(prop.initial_domains())
                self.assertFalse(ok)
                self.assertIsNotNone(prop.failed_run)


if __name__ == "__main__":
    unittest.main()
