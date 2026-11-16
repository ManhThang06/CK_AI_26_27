import unittest

from ..model.board import ClueCell, KakuroBoard
from ..model.cell import Cell
from ..model.constraint import Constraint, Run
from ..model.domains import Domains
from ..solver import SolverFactory
from .helpers import BY_LABEL


class CellTests(unittest.TestCase):
    def test_key_round_trip_and_tuple_behaviour(self):
        cell = Cell(2, 3)
        self.assertEqual(cell.key, "2,3")
        self.assertEqual(Cell.parse("2,3"), cell)
        self.assertEqual(cell, (2, 3))
        self.assertLess(Cell(1, 9), Cell(2, 0))


class DomainsTests(unittest.TestCase):
    def test_fix_and_restore(self):
        cells = [Cell(0, 0), Cell(0, 1)]
        domains = Domains.full(cells)
        before = domains.copy()
        log = []
        domains.fix(cells[0], 4, log)
        self.assertTrue(domains.is_fixed(cells[0]))
        self.assertEqual(domains.value(cells[0]), 4)
        self.assertEqual(domains.unassigned(), [cells[1]])
        self.assertEqual(len(log), 8)
        domains.restore(log)
        self.assertEqual(domains, before)

    def test_snapshot_round_trip(self):
        domains = Domains({Cell(0, 1): {3, 1}, Cell(0, 0): {5}})
        snapshot = domains.snapshot()
        self.assertEqual(snapshot, {"0,0": [5], "0,1": [1, 3]})
        self.assertEqual(Domains.from_snapshot(snapshot), domains)

    def test_empty_cells(self):
        domains = Domains({Cell(0, 0): set(), Cell(0, 1): {1}})
        self.assertEqual(domains.empty_cells(), [Cell(0, 0)])


class ConstraintTests(unittest.TestCase):
    def test_run_is_a_constraint(self):
        run = Run("A1", [Cell(0, 0), Cell(0, 1)], 3)
        self.assertIsInstance(run, Constraint)
        self.assertTrue(run.is_satisfied_by([1, 2]))
        self.assertFalse(run.is_satisfied_by([1, 1]))
        self.assertFalse(run.is_satisfied_by([1, 3]))
        self.assertTrue(run.is_feasible())
        self.assertFalse(Run("A2", [Cell(0, 0), Cell(0, 1)], 30).is_feasible())

    def test_filter_prunes_domains(self):
        cells = [Cell(0, 0), Cell(0, 1)]
        domains = Domains.full(cells)
        removed = []
        changed = Run("A1", cells, 3).filter(domains, removed)
        self.assertEqual(changed, cells)
        self.assertEqual(domains[cells[0]], {1, 2})
        self.assertEqual(len(removed), 14)


class BoardTests(unittest.TestCase):
    def test_clue_parsing(self):
        self.assertEqual(ClueCell.parse("d14/a12"), ClueCell(14, 12))
        self.assertEqual(ClueCell.parse("a3"), ClueCell(None, 3))
        with self.assertRaises(ValueError):
            ClueCell.parse("x3")

    def test_board_builds_cells_and_runs(self):
        board = BY_LABEL["5x5"].board
        self.assertIsInstance(board, KakuroBoard)
        self.assertEqual((board.rows, board.cols, len(board.cells)), (5, 5, 12))
        self.assertEqual(len(board.runs), 8)
        self.assertEqual(board.clue_at(1, 1), ClueCell(14, 12))
        self.assertIsNone(board.clue_at(0, 0))
        self.assertTrue(board.is_white(2, 2))
        self.assertFalse(board.is_white(0, 0))


class SolverFactoryTests(unittest.TestCase):
    def test_names_and_create(self):
        self.assertEqual(SolverFactory.variable_names(), ["first", "mrv", "mrv-degree"])
        self.assertEqual(SolverFactory.value_names(), ["asc", "lcv"])
        solver = SolverFactory.create(BY_LABEL["5x5"], "mrv", "asc", max_nodes=50)
        self.assertEqual(solver.config, {"variable": "mrv", "value": "asc", "max_nodes": 50})
        self.assertEqual(solver.solve().status, "solved")


if __name__ == "__main__":
    unittest.main()
