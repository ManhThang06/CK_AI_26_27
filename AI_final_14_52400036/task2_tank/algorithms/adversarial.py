"""Minimax Search và Alpha-Beta Search cho Tank Battle (Lec 07).

Chỉ dùng giao diện GameState của engine: player(), legal_actions(), result(),
is_terminal(), utility(). Một cycle gồm hai ply (MAX chọn rồi MIN chọn) nên cây
tìm kiếm xen kẽ nút MAX và nút MIN, mỗi nút có 6 nhánh.
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict

from ..engine import Action
from ..engine.constants import MOVE_DIRECTION

MAX_PLAYER = 0
MIN_PLAYER = 1


@dataclass
class SearchStats:
    nodes_generated: int = 0     # số lần gọi result() (số nút con được sinh ra)
    nodes_expanded: int = 0      # số nút không kết thúc đã được mở rộng
    cutoff_nodes: int = 0
    terminal_nodes: int = 0      # số nút kết thúc được đánh giá bằng utility()
    pruned_branches: int = 0     # số nhánh con bị bỏ qua nhờ cắt tỉa (chỉ Alpha-Beta)
    cutoffs: int = 0             # số lần cắt tỉa xảy ra (chỉ Alpha-Beta)
    depth_reached: int = 0
    max_depth: int = 0           # độ sâu ply lớn nhất đã chạm tới
    elapsed: float = 0.0         # thời gian chạy (giây)


@dataclass
class SearchResult:
    action: Action
    value: float
    stats: SearchStats
    # Giá trị của từng hành động ở gốc. Với Alpha-Beta, nhánh bị cắt chỉ là cận
    # (không chính xác) vì không cần biết giá trị thật của nó.
    action_values: Dict[Action, float] = field(default_factory=dict)


class SearchTimeout(Exception):
    """Ngắt tìm kiếm khi hết ngân sách suy nghĩ."""


class AdversarialSearch:
    """Lớp cha chứa phần chung: giới hạn cycle, thống kê, sắp xếp nước đi."""

    name = "base"

    TIE_EPS = 1e-9
    MATERIAL_SCALE = 100.0   # điểm vật chất có biên độ tối đa 0.15 với HP chuẩn, luôn nhỏ hơn giá trị thắng/thua (1/-1)

    def __init__(self, move_ordering=False, horizon=None, rng=None, horizon_score=False, deadline=None, tie_breaker=None):
        """
        move_ordering: đưa FIRE lên đầu khi tank đang đối mặt địch (giúp cắt tỉa nhiều hơn).
        horizon: giới hạn số cycle tính từ gốc. None tìm tới terminal thật.
        Tại cutoff, horizon_score bật đánh giá chênh lệch HP, tắt dùng hằng số 0.
        Cutoff được thống kê riêng và không thay đổi điều kiện kết thúc của engine.
        """
        self.deadline = deadline
        self.tie_breaker = tie_breaker
        self.move_ordering = move_ordering
        self.horizon = horizon
        self.rng = rng
        self.horizon_score = horizon_score
        self.cycle_limit = None
        self.stats = SearchStats()

    # ------------------------------------------------------------ nội bộ
    def _begin(self, state):
        self.stats = SearchStats()
        self.cycle_limit = None if self.horizon is None else state.cycle + self.horizon

    def _is_terminal(self, state):
        if state.is_terminal():
            return True
        return (self.cycle_limit is not None and state.pending is None
                and state.cycle >= self.cycle_limit)

    def _terminal_value(self, state):
        """Giá trị của nút kết thúc hoặc nút bị cắt ở horizon."""
        if state.is_terminal() or not self.horizon_score:
            return state.utility()
        t0, t1 = state.tanks
        b0, b1 = state.bases
        return ((t0.hp - t1.hp) + (b0.hp - b1.hp)) / self.MATERIAL_SCALE

    @staticmethod
    def _is_noop(state, action):
        """Hành động không làm đổi gì ở phía người đi: STAY, FIRE khi đạn cũ còn bay, hoặc MOVE
        vào ô bị chắn cứng khi tank đã quay sẵn hướng đó."""
        if action == Action.STAY:
            return True
        me = state.player()
        if action == Action.FIRE:
            return any(b.owner == me for b in state.bullets)
        d = MOVE_DIRECTION.get(action)
        if d is None:
            return False
        t = state.tanks[me]
        return t.direction == d and state._blocked(t.x + d.value[0], t.y + d.value[1])

    def _pick(self, state, values, order):
        """Chọn nước đi tốt nhất ở gốc: theo thứ tự đầu tiên, hoặc ngẫu nhiên giữa các nước bằng điểm."""
        is_max = state.player() == MAX_PLAYER
        best = max(values.values()) if is_max else min(values.values())
        tied = [a for a in order if values[a] == best]
        if self.tie_breaker is not None and len(tied) > 1:
            return self.tie_breaker(state, tied), best
        if self.rng is None or len(tied) == 1:
            return tied[0], best
        useful = [a for a in tied if not self._is_noop(state, a)]
        return self.rng.choice(useful or tied), best

    def _ordered_actions(self, state):
        actions = state.legal_actions()
        if not self.move_ordering:
            return actions
        me = state.player()
        tank = state.tanks[me]
        enemy_tank = state.tanks[1 - me]
        enemy_base = state.bases[1 - me]
        if (self._facing(tank, enemy_tank.x, enemy_tank.y)
                or self._facing(tank, enemy_base.x, enemy_base.y)):
            return [Action.FIRE] + [a for a in actions if a != Action.FIRE]
        return actions

    @staticmethod
    def _facing(tank, tx, ty):
        """Tank có đang quay thẳng về ô (tx, ty) trên cùng hàng/cột không (bỏ qua vật cản)."""
        fx, fy = tank.direction.value
        dx, dy = tx - tank.x, ty - tank.y
        if fy == 0:
            return dy == 0 and dx != 0 and (dx > 0) == (fx > 0)
        return dx == 0 and dy != 0 and (dy > 0) == (fy > 0)

    def _check_deadline(self):
        if self.deadline is not None and time.perf_counter() >= self.deadline:
            raise SearchTimeout

    # ------------------------------------------------------------ API
    def search(self, state) -> SearchResult:
        """Trả về hành động tốt nhất cho người đang đến lượt tại `state`."""
        raise NotImplementedError


class MinimaxSearch(AdversarialSearch):
    """Minimax duyệt đầy đủ cây trong phạm vi terminal hoặc horizon đã chọn."""

    name = "Minimax"

    def search(self, state):
        self._begin(state)
        start = time.perf_counter()
        values = {}
        order = self._ordered_actions(state)

        for a in order:
            self.stats.nodes_generated += 1
            values[a] = self._value(state.result(a), 1)

        best_action, best_value = self._pick(state, values, order)
        self.stats.nodes_expanded += 1  # nút gốc
        self.stats.elapsed = time.perf_counter() - start
        return SearchResult(best_action, best_value, self.stats, values)

    def _value(self, state, depth):
        self._check_deadline()
        stats = self.stats
        if depth > stats.max_depth:
            stats.max_depth = depth

        if self._is_terminal(state):
            if state.is_terminal():
                stats.terminal_nodes += 1
            else:
                stats.cutoff_nodes += 1
            return self._terminal_value(state)

        stats.nodes_expanded += 1
        if state.player() == MAX_PLAYER:
            v = -math.inf
            for a in self._ordered_actions(state):
                stats.nodes_generated += 1
                v = max(v, self._value(state.result(a), depth + 1))
            return v
        v = math.inf
        for a in self._ordered_actions(state):
            stats.nodes_generated += 1
            v = min(v, self._value(state.result(a), depth + 1))
        return v


class AlphaBetaSearch(AdversarialSearch):
    """Alpha-Beta: cùng giá trị gốc như Minimax nhưng bỏ qua các nhánh không ảnh hưởng quyết định.

    Ở nút MAX cắt khi v >= beta, ở nút MIN cắt khi v <= alpha.
    """

    name = "Alpha-Beta"

    def search(self, state):
        self._begin(state)
        start = time.perf_counter()
        is_max = state.player() == MAX_PLAYER
        alpha, beta = -math.inf, math.inf
        best_value = None
        values = {}
        order = self._ordered_actions(state)
        # Khi chọn ngẫu nhiên giữa các nước bằng điểm, cần biết giá trị CHÍNH XÁC của nước bằng điểm
        # tốt nhất; cửa sổ nới thêm TIE_EPS để nhánh bằng điểm không bị cắt thành cận.
        eps = self.TIE_EPS if self.rng is not None else 0.0

        for a in order:
            self.stats.nodes_generated += 1
            v = self._value(state.result(a), alpha, beta, 1)
            values[a] = v
            if is_max:
                if best_value is None or v > best_value:
                    best_value = v
                alpha = max(alpha, best_value - eps)
            else:
                if best_value is None or v < best_value:
                    best_value = v
                beta = min(beta, best_value + eps)

        best_action, best_value = self._pick(state, values, order)
        self.stats.nodes_expanded += 1  # nút gốc
        self.stats.elapsed = time.perf_counter() - start
        return SearchResult(best_action, best_value, self.stats, values)

    def _value(self, state, alpha, beta, depth):
        self._check_deadline()
        stats = self.stats
        if depth > stats.max_depth:
            stats.max_depth = depth

        if self._is_terminal(state):
            if state.is_terminal():
                stats.terminal_nodes += 1
            else:
                stats.cutoff_nodes += 1
            return self._terminal_value(state)

        stats.nodes_expanded += 1
        actions = self._ordered_actions(state)
        n = len(actions)

        if state.player() == MAX_PLAYER:
            v = -math.inf
            for i, a in enumerate(actions):
                stats.nodes_generated += 1
                v = max(v, self._value(state.result(a), alpha, beta, depth + 1))
                if v >= beta:
                    stats.cutoffs += 1
                    stats.pruned_branches += n - i - 1
                    return v
                alpha = max(alpha, v)
            return v

        v = math.inf
        for i, a in enumerate(actions):
            stats.nodes_generated += 1
            v = min(v, self._value(state.result(a), alpha, beta, depth + 1))
            if v <= alpha:
                stats.cutoffs += 1
                stats.pruned_branches += n - i - 1
                return v
            beta = min(beta, v)
        return v