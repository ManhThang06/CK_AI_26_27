from .constants import (Action, Direction, MOVE_DIRECTION, BULLET_SPEED,
                        DAMAGE, MAX_CYCLES, WALL_HP)
from .entities import Tank, Base, Bullet

class GameState:
    def __init__(self, width, height, walls, tanks, bases, bullets, cycle, pending):
        self.width = width
        self.height = height
        self.walls = walls      
        self.tanks = tanks      
        self.bases = bases      
        self.bullets = bullets  
        self.cycle = cycle
        self.pending = pending  

    @staticmethod
    def from_map(game_map):
        walls = {pos: WALL_HP for pos in game_map.walls}
        (x1, y1), (x2, y2) = game_map.tank_pos
        tanks = [Tank(x1, y1, GameState._face(x1, y1, x2, y2)),
                 Tank(x2, y2, GameState._face(x2, y2, x1, y1))]
        bases = [Base(*game_map.base_pos[0]), Base(*game_map.base_pos[1])]
        return GameState(game_map.width, game_map.height, walls,
                         tanks, bases, [], 0, None)

    @staticmethod
    def _face(x, y, tx, ty):
        
        if tx != x:
            return Direction.RIGHT if tx > x else Direction.LEFT
        return Direction.DOWN if ty > y else Direction.UP

    def clone(self):
        return GameState(self.width, self.height, dict(self.walls),
                         [self.tanks[0].clone(), self.tanks[1].clone()],
                         [self.bases[0].clone(), self.bases[1].clone()],
                         [b.clone() for b in self.bullets] if self.bullets else [],
                         self.cycle, self.pending)

    def player(self):
        return 0 if self.pending is None else 1

    def legal_actions(self):
        return list(Action)

    def result(self, action):
        new = self.clone()
        if new.pending is None:
            new.pending = action        
        else:
            new._resolve_cycle(new.pending, action)
        return new

    def is_terminal(self):
        if self.pending is not None:    
            return False
        return self._max_lost() or self._min_lost() or self.cycle >= MAX_CYCLES

    def utility(self):
        max_lost, min_lost = self._max_lost(), self._min_lost()
        if min_lost and not max_lost:
            return 1
        if max_lost and not min_lost:
            return -1
        return 0

    def _max_lost(self):
        return self.tanks[0].hp <= 0 or self.bases[0].hp <= 0

    def _min_lost(self):
        return self.tanks[1].hp <= 0 or self.bases[1].hp <= 0

    def _resolve_cycle(self, action_max, action_min):
        self._move_tanks([action_max, action_min])
        for owner, act in enumerate([action_max, action_min]):
            if act == Action.FIRE:
                self._fire(owner)
        for _ in range(BULLET_SPEED):
            self._advance_bullets()
        self.cycle += 1
        self.pending = None

    def _blocked(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True
        if (x, y) in self.walls:
            return True
        b0, b1 = self.bases
        return (b0.x == x and b0.y == y) or (b1.x == x and b1.y == y)

    def _move_tanks(self, actions):
        old = [(t.x, t.y) for t in self.tanks]
        new = list(old)
        for i, act in enumerate(actions):
            if act in MOVE_DIRECTION:
                d = MOVE_DIRECTION[act]
                self.tanks[i].direction = d     
                nx, ny = old[i][0] + d.value[0], old[i][1] + d.value[1]
                if not self._blocked(nx, ny):
                    new[i] = (nx, ny)
        if new[0] == new[1] or (new[0] == old[1] and new[1] == old[0]):
            new = old
        for i in range(2):
            self.tanks[i].x, self.tanks[i].y = new[i]

    def _fire(self, owner):
        if any(b.owner == owner for b in self.bullets):
            return                              
        t = self.tanks[owner]
        self.bullets.append(Bullet(t.x, t.y, t.direction, owner))

    def _advance_bullets(self):
        alive = []
        for b in self.bullets:
            x, y = b.x + b.direction.value[0], b.y + b.direction.value[1]
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue                       
            if self._hit(x, y):
                continue                       
            b.x, b.y = x, y
            alive.append(b)
        self.bullets = alive

    def _hit(self, x, y):
        if (x, y) in self.walls:
            self.walls[(x, y)] -= DAMAGE
            if self.walls[(x, y)] <= 0:
                del self.walls[(x, y)]
            return True
        for t in self.tanks:
            if t.x == x and t.y == y:
                t.hp -= DAMAGE
                return True
        for b in self.bases:
            if b.x == x and b.y == y:
                b.hp -= DAMAGE
                return True
        return False
