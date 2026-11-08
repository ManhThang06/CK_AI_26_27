"""Agent điều khiển tank bằng tìm kiếm đối kháng.

choose_action(state) trả về Action cho người đang đến lượt tại `state`
(MAX nếu state.player() == 0, ngược lại là MIN).
"""

import time
from abc import ABC, abstractmethod

from .adversarial import MinimaxSearch, AlphaBetaSearch


class Agent(ABC):
    name = "Agent"

    @abstractmethod
    def choose_action(self, state):
        """Trả về một Action hợp lệ."""


class SearchAgent(Agent):
    search_cls = None

    def __init__(self, horizon=None, move_ordering=False):
        self.horizon = horizon
        self.move_ordering = move_ordering
        self.last_result = None

    @property
    def name(self):
        label = self.search_cls.name
        if self.horizon is not None:
            label += " (h=%d cycle)" % self.horizon
        if self.move_ordering:
            label += " +ordering"
        return label

    def choose_action(self, state):
        search = self.search_cls(move_ordering=self.move_ordering, horizon=self.horizon)
        self.last_result = search.search(state)
        return self.last_result.action


class MinimaxAgent(SearchAgent):
    search_cls = MinimaxSearch


class AlphaBetaAgent(SearchAgent):
    search_cls = AlphaBetaSearch


def play_match(state, agent_max, agent_min, verbose=False):
    """Chạy một ván từ `state`: MAX chọn trước, MIN chọn sau và biết hành động của MAX.

    Trả về (state cuối, utility cho MAX, thời gian suy nghĩ của MAX, của MIN).
    """
    agents = (agent_max, agent_min)
    think = [0.0, 0.0]
    while not state.is_terminal():
        for p in (0, 1):
            t0 = time.perf_counter()
            action = agents[p].choose_action(state)
            think[p] += time.perf_counter() - t0
            state = state.result(action)
            if verbose:
                print("cycle %d  %s -> %s" % (state.cycle, "MAX" if p == 0 else "MIN", action.name))
    return state, state.utility(), think[0], think[1]
