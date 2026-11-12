"""Điều khiển một ván Tank Battle, không phụ thuộc pygame (để test và tái sử dụng).

Quy ước của engine: một cycle gồm 2 ply. Ply 1 là hành động của P1 (MAX, state.player() == 0),
ply 2 là hành động của P2 (MIN, state.player() == 1) rồi engine xử lý cả cycle.
"""

import time
from collections import deque

from ..algorithms.scenarios import load_state, set_hp
from ..engine import Action

HP_PRESETS = {
    "Standard (6/9/3)": dict(),
    "Medium (3/3/2)": dict(tank_hp=3, base_hp=3, wall_hp=2),
    "Low (1/1/1)": dict(tank_hp=1, base_hp=1, wall_hp=1),
}
MAP_NAMES = ["small", "medium", "full"]


class SafeAgent:
    """Bọc agent bất kỳ: bắt lỗi, kiểm tra hành động hợp lệ, đo thời gian suy nghĩ."""

    def __init__(self, agent):
        self.agent = agent
        self.last_error = None
        self.last_time = 0.0
        self.total_time = 0.0
        self.last_nodes = None

    def choose_action(self, state):
        t0 = time.perf_counter()
        try:
            action = self.agent.choose_action(state)
            if action not in state.legal_actions():
                raise ValueError("hành động không hợp lệ: %r" % (action,))
            self.last_error = None
        except Exception as exc:
            action = Action.STAY
            self.last_error = "%s: %s" % (type(exc).__name__, exc)
        self.last_time = time.perf_counter() - t0
        self.total_time += self.last_time
        stats = getattr(getattr(self.agent, "last_result", None), "stats", None)
        self.last_nodes = getattr(stats, "nodes_generated", None)
        return action


class GameController:
    def __init__(self, map_name, hp_preset, factories, labels):
        """factories[i]: hàm không tham số trả về agent, hoặc None nếu bên i do người chơi."""
        self.map_name = map_name
        self.hp_preset = hp_preset
        self.factories = factories
        self.labels = labels
        self.initial = set_hp(load_state(map_name), **HP_PRESETS[hp_preset])
        self.max_tank_hp = self.initial.tanks[0].hp
        self.max_base_hp = self.initial.bases[0].hp
        self.max_wall_hp = max(self.initial.walls.values(), default=1)
        self.reset()

    def reset(self):
        self.state = self.initial.clone()
        self.agents = [SafeAgent(f()) if f else None for f in self.factories]
        self.last_actions = [None, None]
        self.events = []          # (x, y, loại) các va chạm của cycle vừa xử lý
        self.events_time = 0.0
        self.log = deque(maxlen=12)
        self.cycle_count = 0

    # ------------------------------------------------------------ trạng thái
    @property
    def to_move(self):
        return self.state.player()

    def is_human(self, p):
        return self.agents[p] is None

    def is_over(self):
        return self.state.is_terminal()

    def result_text(self):
        if not self.is_over():
            return ""
        u = self.state.utility()
        if u > 0:
            return "P1 wins (%s)" % self.labels[0]
        if u < 0:
            return "P2 wins (%s)" % self.labels[1]
        return "Draw"

    # ------------------------------------------------------------ hành động
    def ai_action(self, p):
        """Chạy agent của bên p (gọi được từ thread riêng, không sửa state)."""
        return self.agents[p].choose_action(self.state.clone())

    def apply(self, action):
        prev = self.state
        self.state = prev.result(action)
        if prev.pending is None:
            return
        self.last_actions = [prev.pending, action]
        self.cycle_count = self.state.cycle
        self.events = self._collect_events(prev, self.state)
        self.events_time = time.monotonic() * 1000   # mốc thời gian để renderer vẽ hiệu ứng nổ
        self.log.append("c%d  P1 %s | P2 %s" % (self.state.cycle, prev.pending.name, action.name))

    @staticmethod
    def _collect_events(prev, new):
        ev = []
        for pos, hp in prev.walls.items():
            if new.walls.get(pos, 0) < hp:
                ev.append((pos[0], pos[1], "wall"))
        for i in (0, 1):
            if new.tanks[i].hp < prev.tanks[i].hp:
                ev.append((new.tanks[i].x, new.tanks[i].y, "tank"))
            if new.bases[i].hp < prev.bases[i].hp:
                ev.append((new.bases[i].x, new.bases[i].y, "base"))
        return ev
