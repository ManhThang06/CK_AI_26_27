from enum import Enum

TANK_HP = 6
BASE_HP = 9
WALL_HP = 3
DAMAGE = 1
BULLET_SPEED = 3
MAX_CYCLES = 100

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Action(Enum):
    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    FIRE = 4
    STAY = 5

MOVE_DIRECTION = {
    Action.MOVE_UP: Direction.UP,
    Action.MOVE_DOWN: Direction.DOWN,
    Action.MOVE_LEFT: Direction.LEFT,
    Action.MOVE_RIGHT: Direction.RIGHT,
}