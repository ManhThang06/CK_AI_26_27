import json
import tempfile
import unittest
from pathlib import Path

from ..puzzle import Puzzle, PuzzleRepository, PUZZLE_DIR
from .helpers import BY_LABEL, PUZZLES, LOAD_ERRORS, SOLVABLE, BROKEN


class LoadingTests(unittest.TestCase):
    def test_every_json_in_puzzle_folder_is_loaded(self):
        files = PuzzleRepository().paths()
        self.assertEqual(len(files), 2)
        self.assertEqual(LOAD_ERRORS, [])
        self.assertEqual([p.path for p in PUZZLES], files)

    def test_natural_order_by_size(self):
        self.assertEqual([p.label for p in PUZZLES], ["5x5", "9x9"])

    def test_dimensions_and_variable_counts(self):
        self.assertEqual((BY_LABEL["5x5"].board.rows, len(BY_LABEL["5x5"].cells)), (5, 12))
        self.assertEqual((BY_LABEL["9x9"].board.rows, len(BY_LABEL["9x9"].cells)), (9, 48))

    def test_standard_puzzles_have_no_warnings(self):
        self.assertEqual({p.label for p in SOLVABLE}, {"5x5", "9x9"})
        for p in SOLVABLE:
            self.assertTrue(all(len([r for r in p.runs if c in r.cells]) == 2 for c in p.cells))

    def test_inconsistent_puzzles_load_with_warnings(self):
        self.assertEqual(len(BROKEN), 1)
        for p in BROKEN:
            self.assertTrue(any("vo nghiem" in w for w in p.warnings), p.warnings)
            self.assertTrue(any("chi co 1 o" in w for w in p.warnings), p.warnings)

    def test_check_accepts_only_valid_solutions(self):
        p = BY_LABEL["5x5"]
        good = {"1,2": 8, "1,3": 4, "2,1": 9, "2,2": 3, "2,3": 1, "2,4": 8,
                "3,1": 5, "3,2": 1, "3,3": 2, "3,4": 3, "4,2": 9, "4,3": 7}
        self.assertTrue(p.check(good))
        bad = dict(good, **{"1,2": 4, "1,3": 8})            # van dung tong hang, sai tong cot
        self.assertFalse(p.check(bad))
        self.assertFalse(p.check({k: v for k, v in good.items() if k != "4,3"}))
        self.assertFalse(p.check(dict(good, **{"4,3": 0})))


class BadInputTests(unittest.TestCase):
    def test_malformed_grids_raise_value_error(self):
        cases = {
            "non-rectangular": {"grid": [["#", "#"], ["#"]]},
            "bad token": {"grid": [["x1", "#"], ["#", "#"]]},
            "empty": {"grid": []},
            "no grid": {"name": "x"},
            "white cell without clue": {"grid": [["#", "#"], ["#", "."]]},
        }
        for name, data in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                Puzzle(data)

    def test_load_all_skips_broken_files_but_keeps_the_rest(self):
        good = json.loads(Path(PUZZLE_DIR / "assignment_5x5.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a_good.json").write_text(json.dumps(good), encoding="utf-8")
            (Path(tmp) / "b_not_json.json").write_text("{oops", encoding="utf-8")
            (Path(tmp) / "c_bad_grid.json").write_text(json.dumps({"grid": [["#"], []]}), encoding="utf-8")
            puzzles, errors = PuzzleRepository(tmp).load_all()
        self.assertEqual([p.path.name for p in puzzles], ["a_good.json"])
        self.assertEqual(sorted(Path(p).name for p, _ in errors), ["b_not_json.json", "c_bad_grid.json"])


if __name__ == "__main__":
    unittest.main()
