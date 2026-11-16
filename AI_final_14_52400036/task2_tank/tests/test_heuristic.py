import math
import unittest

from task2_tank.algorithms.heuristic_eval import HeuristicEvaluator, WIN_SCORE, _plan
from task2_tank.algorithms.heuristic_search import HeuristicMinimaxSearch, HeuristicAlphaBetaSearch
from task2_tank.algorithms.scenarios import load_state, warmup


class HeuristicTests(unittest.TestCase):
    def test_cache_does_not_change_value(self):
        state = load_state("medium")
        evaluator = HeuristicEvaluator()
        _plan.cache_clear()
        cold = evaluator.evaluate(state)
        warm = evaluator.evaluate(state)
        self.assertTrue(math.isfinite(cold))
        self.assertEqual(cold, warm)
        self.assertLess(abs(cold), WIN_SCORE - 200)

    def test_search_does_not_mutate_input(self):
        state = load_state("small")
        before = (state.cycle, state.pending, dict(state.walls), [(t.x, t.y, t.hp) for t in state.tanks])
        HeuristicMinimaxSearch(depth=1).search(state)
        after = (state.cycle, state.pending, dict(state.walls), [(t.x, t.y, t.hp) for t in state.tanks])
        self.assertEqual(before, after)

    def test_pruning_preserves_value_for_both_players(self):
        from task2_tank.engine import Action
        state = warmup(load_state("small"), 3, 4)
        for current in (state, state.result(Action.STAY)):
            kwargs = dict(depth=2, move_ordering=False, prune_noop=False, avoid_doomed=False)
            full = HeuristicMinimaxSearch(**kwargs).search(current)
            pruned = HeuristicAlphaBetaSearch(**kwargs).search(current)
            self.assertAlmostEqual(full.value, pruned.value)
            self.assertGreater(full.stats.cutoff_nodes, 0)

    def test_iterative_deepening_keeps_completed_depth(self):
        state = load_state("small")
        from task2_tank.algorithms.heuristic_search import SearchTimeout
        search = HeuristicAlphaBetaSearch(time_limit=1.0, max_depth=3)
        original = search._search_root
        def stop_after_first(current, hint):
            if search.cycle_limit > current.cycle + 1:
                raise SearchTimeout()
            return original(current, hint)
        search._search_root = stop_after_first
        result = search.search(state)
        self.assertEqual(result.stats.depth_reached, 1)
        self.assertIn(result.action, state.legal_actions())
