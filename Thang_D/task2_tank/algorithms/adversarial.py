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

MAX_PLAYER = 0
MIN_PLAYER = 1


@dataclass
class SearchStats:
    nodes_generated: int = 0     # số lần gọi result() (số nút con được sinh ra)
    nodes_expanded: int = 0      # số nút không kết thúc đã được mở rộng
    terminal_nodes: int = 0      # số nút kết thúc được đánh giá bằng utility()
    pruned_branches: int = 0     # số nhánh con bị bỏ qua nhờ cắt tỉa (chỉ Alpha-Beta)
    cutoffs: int = 0             # số lần cắt tỉa xảy ra (chỉ Alpha-Beta)
    max_depth: int = 0           # độ sâu ply lớn nhất đã chạm tới
    elapsed: float = 0.0         # thời gian chạy (giây)


@dataclass
class SearchResult:
    action: Action
    value: int
    stats: SearchStats
    # Giá trị của từng hành động ở gốc. Với Alpha-Beta, nhánh bị cắt chỉ là cận
    # (không chính xác) vì không cần biết giá trị thật của nó.
    action_values: Dict[Action, int] = field(default_factory=dict)


class AdversarialSearch:
    """Lớp cha chứa phần chung: giới hạn cycle, thống kê, sắp xếp nước đi."""

    name = "base"

    def __init__(self, move_ordering=False, horizon=None):
        """
        move_ordering: đưa FIRE lên đầu khi tank đang đối mặt địch (giúp cắt tỉa nhiều hơn).
        horizon: số cycle nhìn trước tính từ trạng thái gốc. Minimax thuần phải duyệt tới nút
                 kết thúc, mà giới hạn 100 cycle của game là quá sâu, nên khi duyệt tới
                 cycle gốc + horizon thì coi như game kết thúc (utility() trả 0 vì chưa bên nào
                 thua, tức là hòa). None nghĩa là chỉ dừng ở trạng thái kết thúc thật của engine.
        """
        self.move_ordering = move_ordering
        self.horizon = horizon
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

    # ------------------------------------------------------------ API
    def search(self, state) -> SearchResult:
        """Trả về hành động tốt nhất cho người đang đến lượt tại `state`."""
        raise NotImplementedError


class MinimaxSearch(AdversarialSearch):
    """Minimax thuần: duyệt toàn bộ cây, không cắt tỉa."""

    name = "Minimax"

    def search(self, state):
        self._begin(state)
        start = time.perf_counter()
        is_max = state.player() == MAX_PLAYER
        best_action, best_value = None, None
        values = {}

        for a in self._ordered_actions(state):
            self.stats.nodes_generated += 1
            v = self._value(state.result(a), 1)
            values[a] = v
            if best_value is None or (v > best_value if is_max else v < best_value):
                best_action, best_value = a, v

        self.stats.nodes_expanded += 1  # nút gốc
        self.stats.elapsed = time.perf_counter() - start
        return SearchResult(best_action, best_value, self.stats, values)

    def _value(self, state, depth):
        stats = self.stats
        if depth > stats.max_depth:
            stats.max_depth = depth

        if self._is_terminal(state):
            stats.terminal_nodes += 1
            return state.utility()

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
        best_action, best_value = None, None
        values = {}

        for a in self._ordered_actions(state):
            self.stats.nodes_generated += 1
            v = self._value(state.result(a), alpha, beta, 1)
            values[a] = v
            if is_max:
                if best_value is None or v > best_value:
                    best_action, best_value = a, v
                alpha = max(alpha, best_value)
            else:
                if best_value is None or v < best_value:
                    best_action, best_value = a, v
                beta = min(beta, best_value)

        self.stats.nodes_expanded += 1  # nút gốc
        self.stats.elapsed = time.perf_counter() - start
        return SearchResult(best_action, best_value, self.stats, values)

    def _value(self, state, alpha, beta, depth):
        stats = self.stats
        if depth > stats.max_depth:
            stats.max_depth = depth

        if self._is_terminal(state):
            stats.terminal_nodes += 1
            return state.utility()

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
