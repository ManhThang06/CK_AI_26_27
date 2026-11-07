# EVAL for Heuristic Minimax. Always scored from MAX's (tank 1) point of view.
from task2_tank.engine.constants import Direction

WIN_SCORE = 1000   # terminal scores are far above any heuristic value


def first_target(state, x, y, direction):
    # follow the line of fire from (x, y); return what a bullet would hit first
    dx, dy = direction.value
    x, y = x + dx, y + dy
    while 0 <= x < state.width and 0 <= y < state.height:
        if (x, y) in state.walls:
            return None                       # a wall absorbs the bullet
        for i, t in enumerate(state.tanks):
            if (t.x, t.y) == (x, y):
                return ("tank", i)
        for i, b in enumerate(state.bases):
            if (b.x, b.y) == (x, y):
                return ("base", i)
        x, y = x + dx, y + dy
    return None


def manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)


class Evaluator:
    def __init__(self, w_tank=10, w_base=6, w_aim=5, w_dist=0.5):
        self.w_tank = w_tank    # tank HP difference
        self.w_base = w_base    # base HP difference
        self.w_aim = w_aim      # who has a clear shot at whom
        self.w_dist = w_dist    # being closer to the enemy base

    def evaluate(self, state):
        if state.is_terminal():
            return WIN_SCORE * state.utility()

        me, foe = state.tanks
        my_base, foe_base = state.bases

        tank_diff = me.hp - foe.hp
        base_diff = my_base.hp - foe_base.hp
        aim = self._aim(state, 0, 1) - self._aim(state, 1, 0)
        closer = (manhattan(foe.x, foe.y, my_base.x, my_base.y)
                  - manhattan(me.x, me.y, foe_base.x, foe_base.y))

        return (self.w_tank * tank_diff + self.w_base * base_diff
                + self.w_aim * aim + self.w_dist * closer)

    @staticmethod
    def _aim(state, shooter, victim):
        # 1 if the shooter's tank is facing the victim's tank or base with a clear line
        t = state.tanks[shooter]
        return 1 if first_target(state, t.x, t.y, t.direction) in (
            ("tank", victim), ("base", victim)) else 0
