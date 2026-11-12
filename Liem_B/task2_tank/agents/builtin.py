"""Agent mac dinh dung de thu GUI khi chua nap agent ngoai."""
import random

from CK_AI_26_27.Liem_B.task2_tank.engine import Action, Direction
from .base_agent import Agent


class RandomAgent(Agent):
    name = "Random"

    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def choose_action(self, state):
        return self.rng.choice(state.legal_actions())


class ChaserAgent(Agent):
    """Tien lai gan tank dich; thang hang/cot voi dich thi ban."""
    name = "Chaser"

    def choose_action(self, state):
        me = state.player()
        t, e = state.tanks[me], state.tanks[1 - me]
        facing = {Direction.UP: (0, -1), Direction.DOWN: (0, 1),
                  Direction.LEFT: (-1, 0), Direction.RIGHT: (1, 0)}[t.direction]
        dx, dy = e.x - t.x, e.y - t.y
        same_line = (dx == 0 and dy != 0) or (dy == 0 and dx != 0)
        if same_line and (dx * facing[0] > 0 or dy * facing[1] > 0):
            return Action.FIRE
        if abs(dx) >= abs(dy) and dx != 0:
            return Action.MOVE_RIGHT if dx > 0 else Action.MOVE_LEFT
        if dy != 0:
            return Action.MOVE_DOWN if dy > 0 else Action.MOVE_UP
        return Action.FIRE
