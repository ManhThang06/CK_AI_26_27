import csv
import os
import tempfile
import unittest

from task2_tank.agents.simple_agents import RandomAgent
from task2_tank.tools.run_experiment import Scenario, play_game, run_experiment, COLUMNS

SMALL = os.path.join(os.path.dirname(__file__), "..", "maps", "small.txt")


class TestHarness(unittest.TestCase):
    def test_play_game_reaches_the_end(self):
        s = Scenario("tiny", SMALL, 5)
        row = play_game(RandomAgent(1), RandomAgent(2), s.new_state())
        self.assertLessEqual(row["cycles"], 5)
        self.assertEqual(row["moves"], row["cycles"])
        self.assertIn(row["result"], (-1, 0, 1))

    def test_csv_rows_and_columns(self):
        out = os.path.join(tempfile.mkdtemp(), "r.csv")
        scenarios = [Scenario("tiny", SMALL, 3)]
        run_experiment(scenarios, {"a": lambda: RandomAgent(7), "b": lambda: RandomAgent(8)},
                       lambda seed: RandomAgent(seed), 4, out)
        with open(out, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 8)
        self.assertEqual(list(rows[0].keys()), COLUMNS)

    def test_same_seed_same_result(self):
        def run():
            out = os.path.join(tempfile.mkdtemp(), "r.csv")
            run_experiment([Scenario("tiny", SMALL, 4)], {"a": lambda: RandomAgent(7)},
                           lambda seed: RandomAgent(seed), 5, out)
            with open(out, encoding="utf-8") as f:
                return [(r["result"], r["cycles"]) for r in csv.DictReader(f)]
        self.assertEqual(run(), run())


if __name__ == "__main__":
    unittest.main()
