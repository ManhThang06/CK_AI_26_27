import math
import random
import unittest

from task2_tank.algorithms.adversarial import MinimaxSearch, AlphaBetaSearch
from task2_tank.algorithms.agents import MinimaxAgent
from task2_tank.algorithms.heuristic_search import HeuristicMinimaxSearch, HeuristicAlphaBetaSearch
from task2_tank.algorithms.scenarios import load_state, warmup
from task2_tank.engine.constants import Action


class PureSearchTests(unittest.TestCase):
    def test_default_is_deterministic_first_action(self):
        # HP chuẩn, horizon nông: mọi nước hòa, giữ hành vi cũ (nước đầu tiên) khi không bật tùy chọn.
        st = load_state("medium")
        r = MinimaxSearch(horizon=1).search(st)
        self.assertEqual(r.action, Action.MOVE_UP)

    def test_randomize_spreads_over_tied_actions_and_skips_noops(self):
        st = load_state("medium")
        rng = random.Random(0)
        picked = {MinimaxSearch(horizon=1, rng=rng).search(st).action for _ in range(80)}
        self.assertTrue(len(picked) >= 3)
        self.assertNotIn(Action.STAY, picked)

    def test_minimax_alphabeta_agree(self):
        for m in ("small", "medium", "full"):
            for seed in (0, 1, 2):
                st = warmup(load_state(m), 4 * seed, seed)
                for hs in (False, True):
                    a = MinimaxSearch(horizon=2, horizon_score=hs).search(st)
                    b = AlphaBetaSearch(horizon=2, horizon_score=hs).search(st)
                    self.assertTrue(math.isclose(a.value, b.value, abs_tol=1e-9))

    def test_heuristic_minimax_alphabeta_agree(self):
        for m in ("small", "medium", "full"):
            for seed in (0, 1, 2):
                st = warmup(load_state(m), 4 * seed, seed)
                kw = dict(depth=2, move_ordering=False, prune_noop=False, avoid_doomed=False)
                a = HeuristicMinimaxSearch(**kw).search(st)
                b = HeuristicAlphaBetaSearch(**kw).search(st)
                self.assertTrue(math.isclose(a.value, b.value, abs_tol=1e-9))

    def test_alphabeta_explores_fewer_nodes(self):
        st = load_state("full")
        a = MinimaxSearch(horizon=2).search(st)
        b = AlphaBetaSearch(horizon=2).search(st)
        self.assertLess(b.stats.nodes_generated, a.stats.nodes_generated)

    def test_horizon_score_never_beats_real_win(self):
        r = MinimaxSearch(horizon=2, horizon_score=True).search(load_state("small"))
        self.assertTrue(abs(r.value) <= 1.0)

    def test_agent_does_not_get_stuck(self):
        st = load_state("full")
        ag = [MinimaxAgent(horizon=1, move_ordering=True, randomize=True, horizon_score=True, seed=s)
              for s in (1, 2)]
        acts = set()
        for _ in range(30):
            for p in (0, 1):
                a = ag[p].choose_action(st)
                acts.add(a)
                st = st.result(a)
        self.assertTrue(len(acts) >= 4)


class EngineTests(unittest.TestCase):
    def test_initial_hp_matches_spec(self):
        st = load_state("small")
        self.assertEqual([t.hp for t in st.tanks], [6, 6])
        self.assertEqual([b.hp for b in st.bases], [9, 9])
        self.assertTrue(all(hp == 3 for hp in st.walls.values()))

    def test_six_actions(self):
        self.assertEqual(len(load_state("small").legal_actions()), 6)

    def test_bullet_moves_three_cells_per_cycle(self):
        from task2_tank.engine import GameMap, GameState
        st = GameState.from_map(GameMap.parse("1.......2\nA.......B"))
        st = st.result(Action.FIRE).result(Action.STAY)
        self.assertEqual((st.bullets[0].x, st.bullets[0].y), (3, 0))

    def test_bullet_damages_and_stops_at_tank(self):
        from task2_tank.engine import GameMap, GameState
        st = GameState.from_map(GameMap.parse("12\nAB"))
        st = st.result(Action.FIRE).result(Action.STAY)
        self.assertEqual(st.tanks[1].hp, 5)
        self.assertEqual(st.bullets, [])


class PluginTests(unittest.TestCase):
    def test_example_plugin_is_loaded(self):
        from task2_tank.gui.agent_registry import build_registry
        specs, errors = build_registry()
        self.assertEqual(errors, [])
        plugin = [s for s in specs if s.source == "plugin"]
        self.assertTrue(plugin)
        agent = plugin[0].factory(1)
        self.assertIn(agent.choose_action(load_state("small")), Action)


if __name__ == "__main__":
    unittest.main()
