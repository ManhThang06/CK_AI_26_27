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
from collections import Counter, deque
from dataclasses import dataclass

from ..engine import Action
from .adversarial import (AdversarialSearch, SearchResult, SearchStats,
                      MAX_PLAYER, SearchTimeout)
from .heuristic_eval import (ACTION_DELTA, WIN_SCORE,
                             HeuristicEvaluator)


@dataclass
class HeuristicStats(SearchStats):
    heuristic_evals: int = 0     # số lần gọi Eval() tại nút lá chạm giới hạn độ sâu


class _HeuristicSearch(AdversarialSearch):
    """Phần chung: giới hạn độ sâu theo cycle, iterative deepening, sắp xếp nước đi, lịch sử vị trí."""

    use_pruning = False

    def __init__(self, depth=2, evaluator=None, move_ordering=True, prune_noop=True,
                 ordering_use_path=True, time_limit=None, max_depth=10, history_len=6,
                 avoid_doomed=True, repeat_window=40):
        if depth < 1 or max_depth < 1:
            raise ValueError("Độ sâu phải dương")
        if time_limit is not None and time_limit <= 0:
            raise ValueError("Ngân sách thời gian phải dương")
        super().__init__(move_ordering=move_ordering, horizon=None)
        self.depth = depth
        self.evaluator = evaluator or HeuristicEvaluator()
        self.prune_noop = prune_noop
        self.ordering_use_path = ordering_use_path
        self.avoid_doomed = avoid_doomed
        self.seen = deque(maxlen=repeat_window)   # chữ ký các trạng thái chung đã gặp ở lượt của mình
        self.repeats = Counter()
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
        # Đếm các lần đã gặp trạng thái chung (không tính lần hiện tại): tránh kẹt giằng co lâu dài.
        # Tank của me chưa di chuyển nên chữ ký ở lượt MIN (pending) trùng chữ ký ranh giới cycle.
        sig = self.evaluator.signature(state)
        self.evaluator.set_repeats(self.repeats)
        self._note_state(sig)

        self.stats = HeuristicStats()
        start = time.perf_counter()
        self._deadline = start + self.time_limit if self.time_limit else None
        depths = range(1, self.max_depth + 1) if self.time_limit else (self.depth,)

        best = SearchResult(Action.STAY, 0.0, self.stats, {})
        hint = None
        for d in depths:
            self.cycle_limit = state.cycle + d
            self._check_time = self._deadline is not None
            try:
                result = self._search_root(state, hint)
            except SearchTimeout:
                break
            best, hint = result, result.action_values
            self.stats.depth_reached = d
            if abs(result.value) >= WIN_SCORE - 100:    # đã thấy thắng/thua cưỡng bức
                break

        self._commit_state()
        if not self.recent or self.recent[-1] != current:
            self.recent.append(current)
        self.stats.elapsed = time.perf_counter() - start
        return SearchResult(best.action, best.value, self.stats, best.action_values)

    # ------------------------------------------------------------ nội bộ
    def _note_state(self, sig):
        """Ghi nhận trạng thái hiện tại SAU khi search xong, để lần search này không tự phạt chính nó."""
        self._pending_sig = sig

    def _commit_state(self):
        sig = self._pending_sig
        if len(self.seen) == self.seen.maxlen:
            old = self.seen[0]
            self.repeats[old] -= 1
            if self.repeats[old] <= 0:
                del self.repeats[old]
        self.seen.append(sig)
        self.repeats[sig] += 1

    def _tick(self):
        s = self.stats
        s.nodes_generated += 1
        if (self._check_time and (s.nodes_generated & 15) == 0
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
            stats.cutoff_nodes += 1
            stats.heuristic_evals += 1
            return self.evaluator.evaluate(state)
        return None

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
                if self.use_pruning and v >= beta:
                    stats.cutoffs += 1
                    stats.pruned_branches += n - i - 1
                    return v
                if self.use_pruning:
                    alpha = max(alpha, v)
            return v

        v = math.inf
        for i, a in enumerate(actions):
            self._tick()
            v = min(v, self._value(state.result(a), alpha, beta, depth + 1))
            if self.use_pruning and v <= alpha:
                stats.cutoffs += 1
                stats.pruned_branches += n - i - 1
                return v
            if self.use_pruning:
                beta = min(beta, v)
        return v

    # ------------------------------------------------------------ sắp xếp và cắt tỉa nước đi
    def _ordered_actions(self, state, hint=None):
        me = state.player()
        actions = state.legal_actions()
        if self.prune_noop:
            kept = [a for a in actions if not self.evaluator.is_noop(state, me, a)]
            actions = kept or actions
        if self.avoid_doomed and state.bullets:
            actions = self._drop_doomed_moves(state, me, actions)
        if self.move_ordering:
            actions = sorted(actions, key=lambda a: -self._score(state, me, a))
        if hint:
            rev = me == MAX_PLAYER
            worst = -math.inf if rev else math.inf
            # sort ổn định: nước đi cùng giá trị giữ thứ tự theo heuristic ở trên (tie-break xác định)
            actions = sorted(actions, key=lambda a: hint.get(a, worst), reverse=rev)
        return actions

    def _drop_doomed_moves(self, state, me, actions):
        """Bỏ các nước chủ động bước vào ô mà đạn đang bay chắc chắn quét qua trong cycle này.

        Tránh kiểu "né xong lại lao vào đường đạn": heuristic (thẳng hàng với base, tiến gần...) đôi khi
        lớn hơn 1 HP bị trừ nên cây tìm kiếm chọn đứng vào đạn. Chỉ loại khi còn nước khác để chọn."""
        ev = self.evaluator
        doomed = ev.doomed_cells(state)
        if not doomed:
            return actions
        t = state.tanks[me]
        kept = []
        for a in actions:
            delta = ACTION_DELTA.get(a)
            if delta is not None:
                dest = (t.x + delta[0], t.y + delta[1])
                if dest in doomed and ev.can_step(state, dest):
                    continue
            kept.append(a)
        return kept or actions

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
        if not ev.can_step(state, dest):
            # Ô đích là biên map / tường / base: tank không dịch chuyển được, chỉ xoay nòng.
            # Không được tính điểm né đạn hay tiến công cho nước này (nếu không, khi mọi nước đều
            # dính đạn nó thắng tie-break và tank quay mặt ra biên map). Chỉ đáng thử khi xoay
            # xong có thể bắn trúng địch; còn lại xếp sau cả STAY để tie-break giữ nguyên hướng nòng.
            hit = ev.hit_toward(state, me, delta)
            if hit is not None and hit[0] in ("tank", "base") and hit[1] != me:
                return 90
            return -12
        lanes = ev.bullet_lanes(state)
        if cur in lanes and dest not in lanes:
            score += 40                           # né khỏi quỹ đạo đạn
        elif cur not in lanes and dest in lanes:
            score -= 40                           # đang an toàn mà lại bước vào quỹ đạo đạn
        if self.ordering_use_path:
            if ev.attack_plan(state, me, dest)[0] < ev.attack_plan(state, me, cur)[0]:
                score += 20                       # tiến gần vị trí bắn base địch hơn
        return score


class HeuristicMinimaxSearch(_HeuristicSearch):
    """Minimax giới hạn độ sâu, đánh giá lá bằng Eval()."""

    name = "Heuristic Minimax"
    use_pruning = False


class HeuristicAlphaBetaSearch(_HeuristicSearch):
    """Cùng cây đánh giá với Heuristic Minimax, bổ sung cắt tỉa Alpha–Beta."""

    name = "Heuristic Alpha-Beta"
    use_pruning = True
