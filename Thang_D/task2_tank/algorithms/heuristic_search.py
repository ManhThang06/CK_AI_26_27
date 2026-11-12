"""Heuristic Minimax và Heuristic Minimax + Alpha-Beta cho Tank Battle (Lec 07).

Khác với Minimax/Alpha-Beta thuần (duyệt tới nút kết thúc), hai lớp này chỉ nhìn trước
`depth` cycle (mỗi cycle gồm 2 ply: MAX rồi MIN) rồi dùng HeuristicEvaluator để ước lượng
giá trị tại nút lá. Nút kết thúc thật vẫn dùng utility(), thắng sớm được điểm cao hơn
(WIN_SCORE - ply) để agent không trì hoãn chiến thắng và thua càng muộn càng tốt.

Tùy chọn:
  time_limit    bật iterative deepening: tăng dần độ sâu tới khi hết thời gian, dùng kết quả
                của độ sâu hoàn chỉnh cuối cùng. None = độ sâu cố định `depth` (dùng cho thí nghiệm
                so sánh công bằng, nên đặt move_ordering=False, prune_noop=False và tắt nhiễu/lịch sử).
  move_ordering sắp xếp nước đi: FIRE trúng địch > né đạn > tiến gần mục tiêu > lùi > STAY.
  prune_noop    bỏ các MOVE không đổi trạng thái (giảm hệ số nhánh).
"""

import math
import time
from collections import deque
from dataclasses import dataclass

from ..engine import Action
from .adversarial import (AdversarialSearch, SearchResult, SearchStats,
                      MAX_PLAYER, MIN_PLAYER)
from .heuristic_eval import (ACTION_DELTA, WIN_SCORE, EvalWeights,
                             HeuristicEvaluator)


@dataclass
class HeuristicStats(SearchStats):
    heuristic_evals: int = 0     # số lần gọi Eval() tại nút lá chạm giới hạn độ sâu
    depth_reached: int = 0       # độ sâu (cycle) hoàn chỉnh lớn nhất đã tìm xong


class SearchTimeout(Exception):
    pass


class _HeuristicSearch(AdversarialSearch):
    """Phần chung: giới hạn độ sâu theo cycle, iterative deepening, sắp xếp nước đi, lịch sử vị trí."""

    use_pruning = False

    def __init__(self, depth=2, evaluator=None, move_ordering=True, prune_noop=True,
                 ordering_use_path=True, time_limit=None, max_depth=10, history_len=6):
        super().__init__(move_ordering=move_ordering, horizon=None)
        self.depth = depth
        self.evaluator = evaluator or HeuristicEvaluator()
        self.prune_noop = prune_noop
        self.ordering_use_path = ordering_use_path
        self.time_limit = time_limit
        self.max_depth = max_depth
        self.recent = deque(maxlen=history_len)   # các ô tank đã đứng ở những lượt trước
        self._recent_owner = None
        self._deadline = None
        self._check_time = False

    # ------------------------------------------------------------ API
    def search(self, state) -> SearchResult:
        me = state.player()
        if self._recent_owner != me:
            self.recent.clear()
            self._recent_owner = me
        tank = state.tanks[me]
        current = (tank.x, tank.y)
        self.evaluator.me = me
        self.evaluator.set_history(self.recent, current)

        self.stats = HeuristicStats()
        start = time.perf_counter()
        self._deadline = start + self.time_limit if self.time_limit else None
        depths = range(1, self.max_depth + 1) if self.time_limit else (self.depth,)

        best, hint = None, None
        for d in depths:
            self.cycle_limit = state.cycle + d
            # độ sâu 1 luôn chạy xong để chắc chắn có kết quả
            self._check_time = self._deadline is not None and d > 1
            try:
                result = self._search_root(state, hint)
            except SearchTimeout:
                break
            best, hint = result, result.action_values
            self.stats.depth_reached = d
            if abs(result.value) >= WIN_SCORE - 100:    # đã thấy thắng/thua cưỡng bức
                break

        if not self.recent or self.recent[-1] != current:
            self.recent.append(current)
        self.stats.elapsed = time.perf_counter() - start
        return SearchResult(best.action, best.value, self.stats, best.action_values)

    # ------------------------------------------------------------ nội bộ
    def _tick(self):
        s = self.stats
        s.nodes_generated += 1
        if (self._check_time and (s.nodes_generated & 255) == 0
                and time.perf_counter() > self._deadline):
            raise SearchTimeout

    def _search_root(self, state, hint):
        is_max = state.player() == MAX_PLAYER
        alpha, beta = -math.inf, math.inf
        best_action, best_value = None, None
        values = {}

        for a in self._ordered_actions(state, hint):
            self._tick()
            v = self._value(state.result(a), alpha, beta, 1)
            values[a] = v
            if is_max:
                if best_value is None or v > best_value:
                    best_action, best_value = a, v
                if self.use_pruning:
                    alpha = max(alpha, best_value)
            else:
                if best_value is None or v < best_value:
                    best_action, best_value = a, v
                if self.use_pruning:
                    beta = min(beta, best_value)

        self.stats.nodes_expanded += 1  # nút gốc
        return SearchResult(best_action, best_value, self.stats, values)

    def _leaf(self, state, depth):
        """Giá trị của nút lá (kết thúc thật hoặc chạm giới hạn độ sâu), ngược lại None."""
        stats = self.stats
        if depth > stats.max_depth:
            stats.max_depth = depth
        if state.is_terminal():
            stats.terminal_nodes += 1
            u = state.utility()
            return 0.0 if u == 0 else math.copysign(WIN_SCORE - depth, u)
        # chỉ cắt ở ranh giới cycle để vị trí tank và đạn đã được cập nhật đầy đủ
        if state.pending is None and state.cycle >= self.cycle_limit:
            stats.heuristic_evals += 1
            return self.evaluator.evaluate(state)
        return None

    def _value(self, state, alpha, beta, depth):
        raise NotImplementedError

    # ------------------------------------------------------------ sắp xếp và cắt tỉa nước đi
    def _ordered_actions(self, state, hint=None):
        me = state.player()
        actions = state.legal_actions()
        if self.prune_noop:
            kept = [a for a in actions if not self.evaluator.is_noop(state, me, a)]
            actions = kept or actions
        if self.move_ordering:
            actions = sorted(actions, key=lambda a: -self._score(state, me, a))
        if hint:
            rev = me == MAX_PLAYER
            worst = -math.inf if rev else math.inf
            # sort ổn định: nước đi cùng giá trị giữ thứ tự theo heuristic ở trên (tie-break xác định)
            actions = sorted(actions, key=lambda a: hint.get(a, worst), reverse=rev)
        return actions

    def _score(self, state, me, a):
        ev = self.evaluator
        if a == Action.STAY:
            return -10
        if a == Action.FIRE:
            if ev.has_bullet_in_flight(state, me):
                return -10                        # engine bỏ qua FIRE khi đạn cũ còn bay
            hit = ev.facing_hit(state, me)
            if hit is None:
                return -5
            kind, owner, _, pos = hit
            if kind == "wall":
                # bắn phá tường chỉ đáng khi tường nằm trên đường tiến công
                return 60 if pos in ev.attack_plan(state, me)[1] else 0
            return 100 if owner != me else -20    # trúng địch / bắn nhầm đồng đội
        # MOVE
        score = 10
        delta = ACTION_DELTA.get(a)
        if delta is None:
            return score
        t = state.tanks[me]
        cur = (t.x, t.y)
        dest = (cur[0] + delta[0], cur[1] + delta[1])
        if cur in ev.bullet_lanes(state) and dest not in ev.bullet_lanes(state):
            score += 40                           # né khỏi quỹ đạo đạn
        if self.ordering_use_path:
            if ev.attack_plan(state, me, dest)[0] < ev.attack_plan(state, me, cur)[0]:
                score += 20                       # tiến gần vị trí bắn base địch hơn
        return score


class HeuristicMinimaxSearch(_HeuristicSearch):
    """Heuristic Minimax: Minimax giới hạn độ sâu, đánh giá nút lá bằng Eval()."""

    name = "Heuristic Minimax"
    use_pruning = False

    def _value(self, state, alpha, beta, depth):
        v = self._leaf(state, depth)
        if v is not None:
            return v

        self.stats.nodes_expanded += 1
        if state.player() == MAX_PLAYER:
            v = -math.inf
            for a in self._ordered_actions(state):
                self._tick()
                v = max(v, self._value(state.result(a), alpha, beta, depth + 1))
            return v
        v = math.inf
        for a in self._ordered_actions(state):
            self._tick()
            v = min(v, self._value(state.result(a), alpha, beta, depth + 1))
        return v


class HeuristicAlphaBetaSearch(_HeuristicSearch):
    """Heuristic Minimax + Alpha-Beta: cùng giá trị gốc như Heuristic Minimax cùng độ sâu,
    nhưng bỏ qua các nhánh không ảnh hưởng quyết định (move ordering giúp cắt tỉa nhiều hơn)."""

    name = "Heuristic Alpha-Beta"
    use_pruning = True

    def _value(self, state, alpha, beta, depth):
        v = self._leaf(state, depth)
        if v is not None:
            return v

        stats = self.stats
        stats.nodes_expanded += 1
        actions = self._ordered_actions(state)
        n = len(actions)

        if state.player() == MAX_PLAYER:
            v = -math.inf
            for i, a in enumerate(actions):
                self._tick()
                v = max(v, self._value(state.result(a), alpha, beta, depth + 1))
                if v >= beta:
                    stats.cutoffs += 1
                    stats.pruned_branches += n - i - 1
                    return v
                alpha = max(alpha, v)
            return v

        v = math.inf
        for i, a in enumerate(actions):
            self._tick()
            v = min(v, self._value(state.result(a), alpha, beta, depth + 1))
            if v <= alpha:
                stats.cutoffs += 1
                stats.pruned_branches += n - i - 1
                return v
            beta = min(beta, v)
        return v
