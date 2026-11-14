"""Tạo trạng thái xuất phát cho thí nghiệm và test, chỉ dùng API của engine."""

import os
import random

from ..engine import GameMap, GameState

MAPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps")


def load_state(map_name):
    return GameState.from_map(GameMap.load(os.path.join(MAPS_DIR, map_name + ".txt")))


def warmup(state, cycles, seed):
    """Chơi ngẫu nhiên có seed vài cycle để có trạng thái giữa ván, giống nhau cho mọi thuật toán."""
    rng = random.Random(seed)
    for _ in range(cycles):
        if state.is_terminal():
            break
        state = state.result(rng.choice(state.legal_actions()))
        state = state.result(rng.choice(state.legal_actions()))
    return state
