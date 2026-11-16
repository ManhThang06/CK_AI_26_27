import unittest

from ..model.cell import Cell
from ..model.constraint import Run
from ..model.domains import Domains
from ..model.propagation import Propagator

COMBOS = Run.COMBINATIONS
from ..solver import BacktrackingSolver
from .helpers import BROKEN, BY_LABEL, SOLVABLE


class CombosTests(unittest.TestCase):
    def test_known_combinations(self):
        self.assertEqual(COMBOS.lookup(2, 3), [frozenset({1, 2})])
        self.assertEqual(COMBOS.lookup(3, 6), [frozenset({1, 2, 3})])
        self.assertEqual(COMBOS.lookup(9, 45), [frozenset(range(1, 10))])
        self.assertEqual(COMBOS.lookup(2, 2), [])                # 2 chu so khac nhau khong the co tong 2

    def test_run_state(self):
        cells = [Cell(0, 0), Cell(0, 1), Cell(0, 2)]
        domains = Domains({cells[0]: {7}, cells[1]: set(range(1, 10)), cells[2]: {1, 2, 3, 4, 5}})
        used, free, rest, combos = Run("A1", cells, 12).state(domains)
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
                prop = Propagator(p.runs)
                domains = prop.initial_domains()
                previous = {c: set(d) for c, d in domains.items()}
                for _ in range(4):
                    ok, _ = prop.propagate_all(domains)
                    self.assertTrue(ok)
                    for cell, d in domains.items():
                        self.assertIn(solution[cell.key], d)
                        self.assertLessEqual(d, previous[cell])
                    previous = {c: set(d) for c, d in domains.items()}

    def test_assign_then_undo_restores_domains_exactly(self):
        p = BY_LABEL["9x9"]
        prop = Propagator(p.runs)
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
        prop = Propagator(p.runs)
        domains = prop.initial_domains()
        prop.propagate_all(domains)
        cell = next(c for c, d in domains.items() if len(d) > 1 and 9 not in d)
        ok, removed = prop.assign(domains, cell, 9)
        self.assertFalse(ok)
        self.assertEqual(removed, [])

    def test_impossible_run_makes_propagate_all_fail(self):
        for p in BROKEN:
            with self.subTest(p.label):
                prop = Propagator(p.runs)
                ok, _ = prop.propagate_all(prop.initial_domains())
                self.assertFalse(ok)
                self.assertIsNotNone(prop.failed_run)


if __name__ == "__main__":
    unittest.main()
