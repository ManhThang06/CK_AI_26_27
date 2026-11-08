import random
import unittest

from task2_tank.engine import GameMap, GameState, Action, Direction
from task2_tank.algorithms import (MinimaxSearch, AlphaBetaSearch, MinimaxAgent, AlphaBetaAgent,
                                   play_match)
from task2_tank.algorithms.scenarios import load_state, set_hp, warmup


class ForcedWinTest(unittest.TestCase):
    def setUp(self):
        # MIN bị kẹt giữa hai tường và đang quay xuống: không thể bắn trả trong cycle này
        # và cũng không thể rời hàng bắn của MAX, nên FIRE thắng chắc
        s = GameState.from_map(GameMap.parse(".#.#.\nA1.2B\n.#.#."))
        s.tanks[1].direction = Direction.DOWN
        set_hp(s, tank_hp=1)
        self.state = s

    def test_both_algorithms_find_the_win(self):
        for cls in (MinimaxSearch, AlphaBetaSearch):
            res = cls(horizon=1).search(self.state)
            self.assertEqual(res.value, 1)
            self.assertEqual(res.action, Action.FIRE)

    def test_search_does_not_modify_the_state(self):
        before = (self.state.cycle, self.state.pending,
                  [(t.x, t.y, t.hp, t.direction) for t in self.state.tanks])
        AlphaBetaSearch(horizon=2).search(self.state)
        after = (self.state.cycle, self.state.pending,
                 [(t.x, t.y, t.hp, t.direction) for t in self.state.tanks])
        self.assertEqual(before, after)


class EquivalenceTest(unittest.TestCase):
    def test_alpha_beta_matches_minimax(self):
        configs = [
            ("small", dict(tank_hp=1, base_hp=2, wall_hp=1)),
            ("small", dict(tank_hp=2, base_hp=2, wall_hp=2)),
            ("medium", dict(tank_hp=1, base_hp=1, wall_hp=1)),
        ]
        checked = 0
        for map_name, hp in configs:
            for warm in (0, 2, 4):
                for seed in range(5):
                    s = warmup(set_hp(load_state(map_name), **hp), warm, seed)
                    if s.is_terminal():
                        continue
                    for root in (s, s.result(Action.FIRE)):  # gốc MAX và gốc MIN
                        mm = MinimaxSearch(horizon=2).search(root)
                        ab = AlphaBetaSearch(horizon=2).search(root)
                        ab2 = AlphaBetaSearch(horizon=2, move_ordering=True).search(root)
                        self.assertEqual(mm.value, ab.value)
                        self.assertEqual(mm.value, ab2.value)
                        self.assertEqual(mm.action, ab.action)  # cùng thứ tự duyệt, cùng hành động
                        self.assertLessEqual(ab.stats.nodes_generated, mm.stats.nodes_generated)
                        checked += 1
        self.assertGreater(checked, 20)

    def test_alpha_beta_prunes(self):
        s = set_hp(load_state("small"), tank_hp=1, base_hp=1, wall_hp=1)
        mm = MinimaxSearch(horizon=3).search(s)
        ab = AlphaBetaSearch(horizon=3).search(s)
        self.assertEqual(mm.value, ab.value)
        self.assertLess(ab.stats.nodes_generated, mm.stats.nodes_generated)
        self.assertGreater(ab.stats.pruned_branches, 0)


class HorizonTest(unittest.TestCase):
    def test_horizon_counts_from_root_cycle(self):
        s = warmup(load_state("small"), 3, 0)
        res = MinimaxSearch(horizon=1).search(s)
        self.assertEqual(res.stats.max_depth, 2)  # 1 cycle = 2 ply
        root_min = s.result(Action.STAY)
        self.assertEqual(MinimaxSearch(horizon=1).search(root_min).stats.max_depth, 1)

    def test_node_count_matches_branching_factor(self):
        # Không có nút kết thúc sớm: horizon 2 cycle = 4 ply -> 6 + 36 + 216 + 1296 nút con
        s = load_state("small")
        res = MinimaxSearch(horizon=2).search(s)
        self.assertEqual(res.stats.nodes_generated, 6 + 36 + 216 + 1296)

    def test_search_can_start_from_min_ply(self):
        s = load_state("small").result(Action.STAY)
        for cls in (MinimaxSearch, AlphaBetaSearch):
            res = cls(horizon=1).search(s)
            self.assertIn(res.action, s.legal_actions())


class AgentTest(unittest.TestCase):
    def test_full_game_against_each_other(self):
        s = set_hp(load_state("small"), tank_hp=1, base_hp=1, wall_hp=1)
        final, utility, _, _ = play_match(s, AlphaBetaAgent(horizon=2, move_ordering=True),
                                          MinimaxAgent(horizon=2))
        self.assertTrue(final.is_terminal())
        self.assertIn(utility, (-1, 0, 1))


if __name__ == "__main__":
    unittest.main()
