import time
import unittest

from task2_tank.engine import GameMap, GameState, Action, Direction
from task2_tank.agents.evaluation import Evaluator, WIN_SCORE, first_target

BOARD = """
A.....B
1.....2
.......
"""


def make(text=BOARD):
    return GameState.from_map(GameMap.parse(text))


class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.ev = Evaluator()

    def test_win_draw_loss_order(self):
        win, draw, loss = make(), make(), make()
        win.tanks[1].hp = 0
        loss.tanks[0].hp = 0
        draw.cycle = 100
        self.assertGreater(self.ev.evaluate(win), self.ev.evaluate(draw))
        self.assertGreater(self.ev.evaluate(draw), self.ev.evaluate(loss))

    def test_terminal_beats_any_heuristic_value(self):
        s = make()
        s.tanks[1].hp = 1                      # enemy almost dead, not yet terminal
        s.tanks[0].direction = Direction.RIGHT
        win = make()
        win.tanks[1].hp = 0
        self.assertGreater(self.ev.evaluate(win), self.ev.evaluate(s))
        self.assertLess(abs(self.ev.evaluate(s)), WIN_SCORE)

    def test_more_tank_hp_is_better(self):
        a, b = make(), make()
        b.tanks[1].hp -= 2
        self.assertGreater(self.ev.evaluate(b), self.ev.evaluate(a))

    def test_more_base_damage_is_better(self):
        a, b = make(), make()
        b.bases[1].hp -= 3
        self.assertGreater(self.ev.evaluate(b), self.ev.evaluate(a))

    def test_clear_shot_is_better(self):
        a = make()
        b = make()
        b.tanks[0].direction = Direction.DOWN   # not aiming at the enemy any more
        self.assertGreater(self.ev.evaluate(a), self.ev.evaluate(b))

    def test_wall_blocks_the_shot(self):
        s = make("A.....B\n1.#...2\n.......")
        self.assertIsNone(first_target(s, 0, 1, Direction.RIGHT))
        self.assertEqual(first_target(make(), 0, 1, Direction.RIGHT), ("tank", 1))

    def test_symmetric_start_is_zero(self):
        self.assertEqual(self.ev.evaluate(make()), 0)

    def test_being_shot_at_is_worse(self):
        a = make()
        a.tanks[0].direction = Direction.DOWN    # MAX not aiming, enemy still aims
        self.assertLess(self.ev.evaluate(a), 0)

    def test_fast_enough(self):
        s = make()
        start = time.perf_counter()
        for _ in range(20000):
            self.ev.evaluate(s)
        per_call_us = (time.perf_counter() - start) / 20000 * 1e6
        self.assertLess(per_call_us, 50)


if __name__ == "__main__":
    unittest.main()
