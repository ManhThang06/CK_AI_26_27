from .constants import TANK_HP, BASE_HP

class Tank:
    def __init__(self, x, y, direction, hp=TANK_HP):
        self.x = x
        self.y = y
        self.direction = direction
        self.hp = hp

    def clone(self):
        return Tank(self.x, self.y, self.direction, self.hp)

    def is_alive(self):
        return self.hp > 0

class Base:
    def __init__(self, x, y, hp=BASE_HP):
        self.x = x
        self.y = y
        self.hp = hp

    def clone(self):
        return Base(self.x, self.y, self.hp)

    def is_alive(self):
        return self.hp > 0


class Bullet:
    def __init__(self, x, y, direction, owner):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner = owner  # 0 = tank 1 (MAX), 1 = tank 2 (MIN)

    def clone(self):
        return Bullet(self.x, self.y, self.direction, self.owner)
