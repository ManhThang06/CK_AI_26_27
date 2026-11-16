import random
import time
from collections import Counter, deque
from abc import ABC, abstractmethod

from .adversarial import MinimaxSearch, AlphaBetaSearch, SearchResult, SearchStats, SearchTimeout
from .heuristic_search import HeuristicMinimaxSearch, HeuristicAlphaBetaSearch
from .heuristic_eval import HeuristicEvaluator
from ..engine import Action


class Agent(ABC):
    name = "Agent"

    @abstractmethod
    def choose_action(self, state):
        """Trả về một Action hợp lệ."""


class SearchAgent(Agent):
    search_cls = None

    def __init__(self, horizon=None, move_ordering=False, randomize=False, horizon_score=False, seed=None, time_limit=None, tactical_ties=False):
        self.time_limit = time_limit
        self.tactical_ties = tactical_ties
        self.recent = deque(maxlen=12)
        self.seen = deque(maxlen=40)
        self.tie_evaluator = HeuristicEvaluator()
        self.horizon = horizon
        self.move_ordering = move_ordering
        self.horizon_score = horizon_score
        self.rng = random.Random(seed) if randomize else None
        self.last_result = None

    @property
    def name(self):
        label = self.search_cls.name
        if self.horizon is not None:
            label += " (h=%d cycle)" % self.horizon
        if self.move_ordering:
            label += " +ordering"
        if self.rng is not None:
            label += " +random-tie"
        if self.horizon_score:
            label += " +hp-score"
        return label

    def _make_search(self):
        return self.search_cls(move_ordering=self.move_ordering, horizon=self.horizon,
                                 rng=self.rng, horizon_score=self.horizon_score,
                                 tie_breaker=self._choose_tie if self.tactical_ties else None)

    def _choose_tie(self, state, actions):
        """Phá hòa ở gốc bằng đánh giá một cycle và lịch sử, giữ điểm minimax làm tiêu chí chính."""
        me = state.player()
        evaluator = self.tie_evaluator
        evaluator.me = me
        current = (state.tanks[me].x, state.tanks[me].y)
        evaluator.set_history(self.recent, current)
        evaluator.set_repeats(Counter(self.seen))
        scores = {}
        for action in actions:
            child = state.result(action)
            if child.pending is not None:
                replies = [child.result(reply) for reply in child.legal_actions()]
                scores[action] = min(evaluator.evaluate(reply) if not reply.is_terminal()
                                     else reply.utility() * 10000 for reply in replies)
            else:
                scores[action] = (child.utility() * 10000 if child.is_terminal()
                                  else evaluator.evaluate(child))
        best = max(scores.values()) if me == 0 else min(scores.values())
        tied = [action for action in actions if scores[action] == best]
        return self.rng.choice(tied) if self.rng is not None else tied[0]

    def choose_action(self, state):
        start = time.perf_counter()
        search = self._make_search()
        if self.time_limit is None:
            result = search.search(state)
        else:
            result = SearchResult(Action.STAY, 0.0, SearchStats(), {})
            deadline = start + self.time_limit
            completed_depth = 0
            for depth in range(1, (self.horizon or 3) + 1):
                search.horizon = depth
                search.deadline = deadline
                try:
                    candidate = search.search(state)
                except SearchTimeout:
                    break
                result = candidate
                completed_depth = depth
            result.stats.depth_reached = completed_depth
        result.stats.elapsed = time.perf_counter() - start
        self.last_result = result
        if self.tactical_ties:
            tank = state.tanks[state.player()]
            self.recent.append((tank.x, tank.y))
            self.seen.append(self.tie_evaluator.signature(state))
        return result.action


class MinimaxAgent(SearchAgent):
    search_cls = MinimaxSearch


class AlphaBetaAgent(SearchAgent):
    search_cls = AlphaBetaSearch


class HeuristicAgent(SearchAgent):
    """Bọc HeuristicMinimaxSearch / HeuristicAlphaBetaSearch.

    Mỗi bên giữ một đối tượng search riêng vì search nhớ các ô đã đứng (chống đi lòng vòng).
    """

    search_cls = None
    label = "Heuristic"

    def __init__(self, depth=2, time_limit=None):
        self.depth = depth
        self.search = self.search_cls(depth=depth, time_limit=time_limit, max_depth=depth)
        self.last_result = None

    @property
    def name(self):
        return "%s (d=%d)" % (self.label, self.depth)

    def _make_search(self):
        return self.search

    def choose_action(self, state):
        self.last_result = self._make_search().search(state)
        return self.last_result.action


class HeuristicMinimaxAgent(HeuristicAgent):
    search_cls = HeuristicMinimaxSearch
    label = "Heuristic Minimax"


class HeuristicAlphaBetaAgent(HeuristicAgent):
    search_cls = HeuristicAlphaBetaSearch
    label = "Heuristic Alpha-Beta"


class RandomAgent(Agent):
    name = "Random"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def choose_action(self, state):
        return self.rng.choice(state.legal_actions())


def play_match(state, agent_max, agent_min, verbose=False):
    """API demo dùng cùng bộ điều khiển trận với GUI và giải đấu."""
    from ..engine.match import MatchSession

    match = MatchSession(state, [agent_max, agent_min])
    final = match.run(verbose=verbose)
    return final, final.utility(), match.agents[0].total_time, match.agents[1].total_time
