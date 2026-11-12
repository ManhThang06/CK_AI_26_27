"""Agent demo dong vai 'agent cua nhom khac': chi biet interface, khong sua engine.

Chien thuat: dung yen, quay mat ve phia tank dich, ban khi thang hang.
"""
from CK_AI_26_27.Liem_B.task2_tank.engine import Action, Direction
from CK_AI_26_27.Liem_B.task2_tank.agents.base_agent import Agent


class CornerCamper(Agent):
    name = "CornerCamper(external)"

    def choose_action(self, state):
        me = state.player()
        t, e = state.tanks[me], state.tanks[1 - me]
        dx, dy = e.x - t.x, e.y - t.y
        want = None
        if dy == 0 and dx != 0:
            want = Direction.RIGHT if dx > 0 else Direction.LEFT
        elif dx == 0 and dy != 0:
            want = Direction.DOWN if dy > 0 else Direction.UP
        if want is None:
            return Action.STAY
        if t.direction == want:
            return Action.FIRE
        return {Direction.UP: Action.MOVE_UP, Direction.DOWN: Action.MOVE_DOWN,
                Direction.LEFT: Action.MOVE_LEFT, Direction.RIGHT: Action.MOVE_RIGHT}[want]
