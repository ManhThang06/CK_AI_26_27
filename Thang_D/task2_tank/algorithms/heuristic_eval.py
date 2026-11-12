"""Hàm đánh giá heuristic cho Tank Battle (dùng cho Heuristic Minimax, Lec 07).

Eval(s) luôn tính từ góc nhìn của MAX (người chơi 0): dương nghĩa là MAX đang lợi thế.
Mỗi đặc trưng có dạng f(MAX) - f(MIN) nên hàm đánh giá là zero-sum.

Các đặc trưng:
  base_hp   chênh lệch HP base
  tank_hp   chênh lệch HP tank
  attack    chênh lệch chi phí đường đi tới vị trí bắn được base đối phương
            (Dijkstra, ô tường tốn 1 + HP tường: số phát bắn để phá rồi đi vào)
  fire      tank đang quay đúng hướng và đường bắn thông tới tank/base địch
  aligned   cùng hàng/cột, đường bắn thông nhưng chưa quay đúng hướng (trọng số nhỏ)
  bullet    đạn đang bay sẽ trúng tank/base của ai, nhân 1/(số cycle đạn cần để tới)
  mobility  số ô lân cận có thể bước vào
  wall      tường quanh base, bỏ qua tường nằm trên đường tiến công của hai bên
            (chống tự khóa, tránh tính hai lần) và giảm trọng số khi bên đó đang dẫn trước
Ngoài ra có phạt quay lại ô cũ (chống oscillation) và nhiễu nhỏ có seed.

GIẢ ĐỊNH VỀ ENGINE: mọi chỗ đọc dữ liệu thô nằm trong StateView và ACTION_DELTA bên dưới,
nếu engine đặt tên khác thì chỉ cần sửa hai chỗ này.
"""

import heapq
import math
import random
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from .adversarial import (MAX_PLAYER, MIN_PLAYER)

from ..engine import Action, Direction

WIN_SCORE = 10_000.0     # giá trị thắng; thắng sớm được WIN_SCORE - depth
PATH_CAP = 60.0          # chặn trên chi phí đường đi (khi không có đường)
DIRS = ((0, -1), (0, 1), (-1, 0), (1, 0))

# Độ dời (dx, dy) của từng hành động di chuyển, cùng quy ước với tank.direction.value.
ACTION_DELTA = {
    Action.MOVE_UP: (0, -1),
    Action.MOVE_DOWN: (0, 1),
    Action.MOVE_LEFT: (-1, 0),
    Action.MOVE_RIGHT: (1, 0),
}


class StateView:
    """Lớp mỏng đọc dữ liệu từ GameState (khớp engine/game_state.py).

    state.width, state.height; state.walls là dict {(x, y): hp};
    state.bullets là danh sách Bullet có .x, .y, .direction (Enum, .value = (dx, dy)), .owner;
    state.tanks[i] có .x, .y, .hp, .direction; state.bases[i] có .x, .y, .hp;
    state.cycle và state.pending (None tại ranh giới cycle).
    """

    @staticmethod
    def size(state):
        return state.width, state.height

    @staticmethod
    def walls(state):
        return state.walls

    @staticmethod
    def bullets(state):
        return state.bullets


# ---------------------------------------------------------------- hình học trên lưới
def _entities(state):
    ents = {}
    for i in (0, 1):
        t, b = state.tanks[i], state.bases[i]
        ents[(t.x, t.y)] = ("tank", i)
        ents[(b.x, b.y)] = ("base", i)
    return ents


def first_hit(walls, ents, size, x, y, dx, dy):
    """Đi từ ô kế tiếp (x, y) theo (dx, dy). Trả (loại, chủ, số bước, ô) của vật đầu tiên, hoặc None."""
    w, h = size
    steps = 0
    while True:
        x += dx
        y += dy
        steps += 1
        if not (0 <= x < w and 0 <= y < h):
            return None
        if (x, y) in walls:
            return ("wall", None, steps, (x, y))
        e = ents.get((x, y))
        if e is not None:
            return (e[0], e[1], steps, (x, y))


def _line_clear(walls, ents, size, src, dst):
    """src và dst cùng hàng/cột và không có vật nào chắn giữa."""
    sx, sy = src
    tx, ty = dst
    if sx == tx and sy != ty:
        dx, dy = 0, (1 if ty > sy else -1)
    elif sy == ty and sx != tx:
        dx, dy = (1 if tx > sx else -1), 0
    else:
        return False
    hit = first_hit(walls, ents, size, sx, sy, dx, dy)
    return hit is not None and hit[3] == dst


@lru_cache(maxsize=8192)
def _plan(wall_key, size, src, target, bases):
    """Chi phí ngắn nhất từ src tới một ô bắn được `target` và tập tường nằm trên đường đó.

    Vào một ô tường tốn 1 + HP tường (HP phát bắn để phá, thêm 1 bước đi). Ô base không đi qua được.
    Sau khi tới ô thẳng hàng với target, cộng thêm HP các tường nằm giữa (số phát bắn cần để mở đường bắn).
    Tank được bỏ qua (không coi là vật cản đường đi).
    """
    walls = dict(wall_key)
    w, h = size
    inf = math.inf
    dist = {src: 0}
    parent = {}
    heap = [(0, src)]
    while heap:
        d, cell = heapq.heappop(heap)
        if d > dist.get(cell, inf):
            continue
        x, y = cell
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if not (0 <= n[0] < w and 0 <= n[1] < h) or n in bases:
                continue
            nd = d + 1 + walls.get(n, 0)
            if nd < dist.get(n, inf):
                dist[n] = nd
                parent[n] = cell
                heapq.heappush(heap, (nd, n))

    tx, ty = target
    best, best_cell = inf, None
    for (cx, cy), d in dist.items():
        if cx == tx and cy != ty:
            dx, dy = 0, (1 if ty > cy else -1)
        elif cy == ty and cx != tx:
            dx, dy = (1 if tx > cx else -1), 0
        else:
            continue
        shots = 0
        x, y = cx + dx, cy + dy
        while (x, y) != target:
            if (x, y) in bases:       # base còn lại chắn đường bắn
                shots = inf
                break
            shots += walls.get((x, y), 0)
            x += dx
            y += dy
        if d + shots < best:
            best, best_cell = d + shots, (cx, cy)

    if best_cell is None:
        return PATH_CAP, frozenset()

    path_walls = set()
    cell = best_cell
    while cell != src:
        if cell in walls:
            path_walls.add(cell)
        cell = parent[cell]
    dx = (tx > best_cell[0]) - (tx < best_cell[0])
    dy = (ty > best_cell[1]) - (ty < best_cell[1])
    x, y = best_cell[0] + dx, best_cell[1] + dy
    while (x, y) != target:
        if (x, y) in walls:
            path_walls.add((x, y))
        x += dx
        y += dy
    return min(best, PATH_CAP), frozenset(path_walls)


# ---------------------------------------------------------------- trọng số
@dataclass
class EvalWeights:
    base_hp: float = 10.0
    tank_hp: float = 6.0
    attack: float = 4.0
    fire: float = 15.0
    aligned: float = 4.0
    bullet: float = 20.0
    mobility: float = 2.0
    wall: float = 0.5         # nhỏ: chỉ là tie-break, việc phá tường đã nằm trong chi phí đường đi
    history: float = 1.5      # phạt mỗi lần ô đó đã xuất hiện trong lịch sử gần đây
    noise: float = 0.0        # biên độ nhiễu tie-break, 0 = tắt (dùng khi chạy thí nghiệm)
    lead_discount: float = 0.25   # hệ số giảm bảo vệ tường khi đang dẫn trước (tổng tiến công)
    use_history: bool = True      # cờ ablation: phạt quay lại ô cũ
    use_wall_role: bool = True    # cờ ablation: phân biệt tường chắn đường và phase-aware


class HeuristicEvaluator:
    """Tính Eval(s) từ góc nhìn MAX. `me` và lịch sử chỉ dùng cho phạt chống oscillation."""

    def __init__(self, weights=None, me=MAX_PLAYER, seed=0):
        self.w = weights or EvalWeights()
        self.me = me
        self.rng = random.Random(seed)
        self.history = Counter()
        self.current = None

    def set_history(self, recent_positions, current_position):
        """Các ô tank của `me` đã đứng ở những lượt trước và ô đang đứng hiện tại."""
        self.history = Counter(recent_positions)
        self.current = current_position

    # ------------------------------------------------------------ ngữ cảnh
    def _ctx(self, state):
        walls = StateView.walls(state)
        size = StateView.size(state)
        ents = _entities(state)
        bases = frozenset((b.x, b.y) for b in state.bases)
        return walls, size, ents, bases

    # ------------------------------------------------------------ đặc trưng
    def features(self, state):
        walls, size, ents, bases = self._ctx(state)
        wkey = frozenset(walls.items())
        tanks, bs = state.tanks, state.bases
        pos = [(tanks[i].x, tanks[i].y) for i in (0, 1)]
        bpos = [(bs[i].x, bs[i].y) for i in (0, 1)]

        # chi phí tiến công của từng bên tới base đối phương
        cost, path = [0.0, 0.0], [None, None]
        for i in (0, 1):
            cost[i], path[i] = _plan(wkey, size, pos[i], bpos[1 - i], bases)

        # đường bắn
        can_hit, aligned = [0, 0], [0, 0]
        for i in (0, 1):
            if self.has_bullet_in_flight(state, i):
                continue          # đạn trước chưa biến mất nên chưa bắn được viên mới
            dx, dy = tanks[i].direction.value
            hit = first_hit(walls, ents, size, pos[i][0], pos[i][1], dx, dy)
            if hit is not None and hit[0] in ("tank", "base") and hit[1] == 1 - i:
                can_hit[i] = 1
            elif (_line_clear(walls, ents, size, pos[i], pos[1 - i])
                  or _line_clear(walls, ents, size, pos[i], bpos[1 - i])):
                aligned[i] = 1

        # đạn đang bay: bullet_on[i] là mức đe dọa lên tank/base của người chơi i
        bullet_on = [0.0, 0.0]
        for bl in StateView.bullets(state):
            dx, dy = bl.direction.value
            hit = first_hit(walls, ents, size, bl.x, bl.y, dx, dy)
            if hit is not None and hit[0] in ("tank", "base"):
                bullet_on[hit[1]] += 1.0 / math.ceil(hit[2] / 3)

        # mobility: số ô lân cận trống
        w_, h_ = size
        mob = [0, 0]
        for i in (0, 1):
            for dx, dy in DIRS:
                n = (pos[i][0] + dx, pos[i][1] + dy)
                if 0 <= n[0] < w_ and 0 <= n[1] < h_ and n not in walls and n not in ents:
                    mob[i] += 1

        # tường quanh base, có xét vai trò của tường
        # Tường nằm trên đường tiến công của BẤT KỲ bên nào không tính là "bảo vệ":
        #  - trên đường của chủ base: chống tự khóa, chủ base cần bắn thủng để ra ngoài;
        #  - trên đường của đối thủ: đã được tính trong chi phí đường đi (attack), tránh tính hai lần
        #    và tránh gradient ngược làm triệt tiêu thưởng khi tiến công.
        use_role = self.w.use_wall_role
        prot, factor = [0.0, 0.0], [1.0, 1.0]
        for i in (0, 1):
            bx, by = bpos[i]
            excluded = (path[i] | path[1 - i]) if use_role else frozenset()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    c = (bx + dx, by + dy)
                    if c in walls and c not in excluded:
                        prot[i] += walls[c]
            # phase-aware: bên đang dẫn trước (tổng tiến công) giảm trọng số giữ tường
            if use_role and cost[i] <= cost[1 - i] and bs[i].hp >= bs[1 - i].hp:
                factor[i] = self.w.lead_discount

        threatened = [bool(can_hit[1 - i]) or bullet_on[i] > 0 for i in (0, 1)]
        return {
            "base_hp": bs[0].hp - bs[1].hp,
            "tank_hp": tanks[0].hp - tanks[1].hp,
            "attack": min(cost[1], PATH_CAP) - min(cost[0], PATH_CAP),
            "fire": can_hit[0] - can_hit[1],
            "aligned": aligned[0] - aligned[1],
            "bullet": bullet_on[1] - bullet_on[0],
            "mobility": mob[0] - mob[1],
            "wall": factor[0] * prot[0] - factor[1] * prot[1],
            "pos": pos,
            "threatened": threatened,
        }

    # ------------------------------------------------------------ Eval
    def evaluate(self, state):
        f = self.features(state)
        w = self.w
        v = (w.base_hp * f["base_hp"] + w.tank_hp * f["tank_hp"] + w.attack * f["attack"]
             + w.fire * f["fire"] + w.aligned * f["aligned"] + w.bullet * f["bullet"]
             + w.mobility * f["mobility"] + w.wall * f["wall"])

        # chống oscillation: phạt quay lại ô cũ khi không bị đe dọa
        if w.use_history and self.history and not f["threatened"][self.me]:
            p = f["pos"][self.me]
            if p != self.current:
                pen = w.history * self.history.get(p, 0)
                v -= pen if self.me == MAX_PLAYER else -pen

        if w.noise > 0:
            v += self.rng.uniform(0.0, w.noise)
        return v

    # ------------------------------------------------------------ tiện ích cho move ordering
    def facing_hit(self, state, p):
        """Vật đầu tiên nằm trên hướng bắn của tank p (xem first_hit), hoặc None."""
        walls, size, ents, _ = self._ctx(state)
        t = state.tanks[p]
        dx, dy = t.direction.value
        return first_hit(walls, ents, size, t.x, t.y, dx, dy)

    def attack_plan(self, state, p, src=None):
        """(chi phí, tập tường trên đường) của tank p, xuất phát từ src (mặc định vị trí hiện tại)."""
        walls, size, _, bases = self._ctx(state)
        t = state.tanks[p]
        b = state.bases[1 - p]
        src = (t.x, t.y) if src is None else src
        return _plan(frozenset(walls.items()), size, src, (b.x, b.y), bases)

    def bullet_lanes(self, state):
        """Tập ô nằm trên quỹ đạo đạn đang bay (tới khi chạm vật đầu tiên)."""
        walls, size, ents, _ = self._ctx(state)
        w, h = size
        lanes = set()
        for bl in StateView.bullets(state):
            dx, dy = bl.direction.value
            x, y = bl.x, bl.y
            while True:
                x += dx
                y += dy
                if not (0 <= x < w and 0 <= y < h):
                    break
                lanes.add((x, y))
                if (x, y) in walls or (x, y) in ents:
                    break
        return lanes

    def has_bullet_in_flight(self, state, p):
        """Engine chỉ cho mỗi bên một viên đạn đang bay (xem GameState._fire)."""
        return any(b.owner == p for b in StateView.bullets(state))

    def is_noop(self, state, p, action):
        """Hành động không làm đổi trạng thái của chính tank p (có thể bỏ khỏi cây tìm kiếm).

        - FIRE khi đạn của p còn đang bay: engine bỏ qua, tương đương STAY.
        - MOVE vào ô bị chắn cứng (biên, tường, base) khi tank đã quay sẵn hướng đó.
          Ô có tank KHÔNG tính là bị chắn cứng: tank kia có thể rời đi trong cùng cycle.
        """
        if action == Action.FIRE:
            return self.has_bullet_in_flight(state, p)
        delta = ACTION_DELTA.get(action)
        if delta is None:
            return False
        walls, size, _, bases = self._ctx(state)
        t = state.tanks[p]
        n = (t.x + delta[0], t.y + delta[1])
        blocked = (not (0 <= n[0] < size[0] and 0 <= n[1] < size[1])
                   or n in walls or n in bases)
        return blocked and tuple(t.direction.value) == delta
