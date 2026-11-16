"""Điều khiển một ván Tank Battle, không phụ thuộc pygame (để test và tái sử dụng).

Quy ước của engine: một cycle gồm 2 ply. Ply 1 là hành động của P1 (MAX, state.player() == 0),
ply 2 là hành động của P2 (MIN, state.player() == 1) rồi engine xử lý cả cycle.
"""

import time
from collections import deque

from ..algorithms.scenarios import load_state
from ..engine.match import MatchSession

MAP_NAMES = ["small", "medium", "full"]


class GameController(MatchSession):
    def __init__(self, map_name, factories, labels):
        """factories[i]: hàm không tham số trả về agent, hoặc None nếu bên i do người chơi."""
        self.map_name = map_name
        self.factories = factories
        self.labels = labels
        self.initial = load_state(map_name)
        self.max_tank_hp = self.initial.tanks[0].hp
        self.max_base_hp = self.initial.bases[0].hp
        self.max_wall_hp = max(self.initial.walls.values(), default=1)
        self.reset()

    def reset(self):
        super().__init__(self.initial, [factory() if factory else None for factory in self.factories])
        self.last_actions = [None, None]
        self.events = []          # (x, y, loại) các va chạm của cycle vừa xử lý
        self.events_time = -10_000.0
        self.prev_state = None    # trạng thái trước cycle vừa xử lý (renderer dùng để làm mượt chuyển động)
        self.log = deque(maxlen=12)
        self.cycle_count = 0

    # ------------------------------------------------------------ trạng thái
    @property
    def to_move(self):
        return self.state.player()

    def is_human(self, p):
        return self.agents[p] is None

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
    def apply(self, action):
        prev = self.state
        if self.is_over():
            return
        super().apply(action)
        if prev.pending is None:
            return
        self.last_actions = [prev.pending, action]
        self.cycle_count = self.state.cycle
        self.prev_state = prev
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
