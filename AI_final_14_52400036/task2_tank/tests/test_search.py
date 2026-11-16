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



class TerminalSearchTests(unittest.TestCase):
    def test_exact_search_without_horizon_matches_at_real_terminal(self):
        from task2_tank.engine import GameMap, GameState
        from task2_tank.engine.constants import MAX_CYCLES
        state = GameState.from_map(GameMap.parse("12\nAB"))
        state.cycle = MAX_CYCLES - 1
        state.tanks[1].hp = 1
        full = MinimaxSearch().search(state)
        pruned = AlphaBetaSearch().search(state)
        self.assertEqual(full.value, 1)
        self.assertEqual(full.value, pruned.value)
        self.assertEqual(full.stats.cutoff_nodes, 0)

class PlayingRegressionTests(unittest.TestCase):
    def test_tactical_ties_progress_against_idle_opponent(self):
        from task2_tank.algorithms.agents import AlphaBetaAgent
        for cls in (MinimaxAgent, AlphaBetaAgent):
            state = load_state("full")
            agent = cls(horizon=2, randomize=True, horizon_score=True,
                        tactical_ties=True, seed=7)
            positions = set()
            for _ in range(30):
                if state.is_terminal():
                    break
                action = agent.choose_action(state)
                state = state.result(action).result(Action.STAY)
                positions.add((state.tanks[0].x, state.tanks[0].y))
            self.assertGreater(len(positions), 4)
            self.assertLess(state.bases[1].hp, 9)

    def test_tactical_tie_break_preserves_primary_search_value(self):
        state = load_state("full")
        plain = MinimaxSearch(horizon=1, horizon_score=True).search(state)
        agent = MinimaxAgent(horizon=1, horizon_score=True, tactical_ties=True)
        agent.choose_action(state)
        self.assertEqual(agent.last_result.value, plain.value)
