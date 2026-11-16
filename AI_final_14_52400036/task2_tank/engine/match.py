"""Điều khiển lượt và đo agent dùng chung cho GUI, demo và giải đấu."""

import time

from .constants import Action


class SafeAgent:
    """Kiểm tra đầu ra và lỗi agent, lưu thời gian của từng quyết định."""

    def __init__(self, agent):
        self.agent = agent
        self.last_error = None
        self.last_time = 0.0
        self.total_time = 0.0
        self.last_nodes = None
        self.last_depth = None
        self.moves = 0

    def choose_action(self, state):
        start = time.perf_counter()
        try:
            action = self.agent.choose_action(state.clone())
            if action not in state.legal_actions():
                raise ValueError("Hành động không hợp lệ %r" % (action,))
            self.last_error = None
        except Exception as exc:
            action = Action.STAY
            self.last_error = "%s: %s" % (type(exc).__name__, exc)
        self.last_time = time.perf_counter() - start
        self.total_time += self.last_time
        self.moves += 1
        stats = getattr(getattr(self.agent, "last_result", None), "stats", None)
        self.last_nodes = getattr(stats, "nodes_generated", None)
        self.last_depth = getattr(stats, "depth_reached", None)
        return action


class MatchSession:
    """Trạng thái và bước chạy chung, độc lập với Pygame."""

    def __init__(self, state, agents):
        self.state = state.clone()
        self.agents = [SafeAgent(agent) if agent is not None else None for agent in agents]
        if len(self.agents) != 2:
            raise ValueError("Một trận phải có đúng hai bên")

    def is_over(self):
        return self.state.is_terminal()

    def ai_action(self, player):
        if self.is_over() or player != self.state.player():
            raise ValueError("Chưa đến lượt agent hoặc trận đã kết thúc")
        agent = self.agents[player]
        if agent is None:
            raise ValueError("Lượt này do người chơi điều khiển")
        return agent.choose_action(self.state)

    def apply(self, action):
        if self.is_over():
            return
        if action not in self.state.legal_actions():
            raise ValueError("Hành động không hợp lệ")
        self.state = self.state.result(action)

    def run(self, verbose=False):
        while not self.is_over():
            player = self.state.player()
            action = self.ai_action(player)
            self.apply(action)
            if verbose:
                print("Cycle %d, %s chọn %s" %
                      (self.state.cycle, "MAX" if player == 0 else "MIN", action.name))
        return self.state
