"""Tạo trạng thái xuất phát cho thí nghiệm và test, chỉ dùng API của engine."""

import os
import random

from ..engine import GameMap, GameState

MAPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps")


def load_state(map_name):
    return GameState.from_map(GameMap.load(os.path.join(MAPS_DIR, map_name + ".txt")))


def set_hp(state, tank_hp=None, base_hp=None, wall_hp=None):
    """Chỉnh HP của trạng thái (engine có HP mặc định 6/9/3 là hằng số).
    Với HP chuẩn cần ít nhất 6 cycle mới phá được một tank, nên thí nghiệm dùng thêm
    HP thấp để cây tìm kiếm nông vẫn chạm được nút thắng/thua."""
    if tank_hp is not None:
        for t in state.tanks:
            t.hp = tank_hp
    if base_hp is not None:
        for b in state.bases:
            b.hp = base_hp
    if wall_hp is not None:
        for pos in state.walls:
            state.walls[pos] = wall_hp
    return state


def warmup(state, cycles, seed):
    """Chơi ngẫu nhiên có seed vài cycle để có trạng thái giữa ván, giống nhau cho mọi thuật toán."""
    rng = random.Random(seed)
    for _ in range(cycles):
        if state.is_terminal():
            break
        state = state.result(rng.choice(state.legal_actions()))
        state = state.result(rng.choice(state.legal_actions()))
    return state
