import unittest
from task2_tank.engine import GameMap, GameState, Action, Direction
from task2_tank.engine.constants import MAX_CYCLES

def make(text):
    return GameState.from_map(GameMap.parse(text))

def play(state, a_max, a_min):
    return state.result(a_max).result(a_min)

OPEN = """
A.......B
1.......2
.........
"""

SMALL = """
A..B
1..2
"""

def wall_at(x):
    row = ["."] * 7
    row[0], row[6], row[x] = "1", "2", "#"
    return make("A.....B\n" + "".join(row))

class TestBasics(unittest.TestCase):
    def test_initial_state(self):
        s = make(OPEN)
        self.assertEqual(s.player(), 0)
        self.assertFalse(s.is_terminal())
        self.assertEqual((s.tanks[0].hp, s.tanks[1].hp), (6, 6))
        self.assertEqual((s.bases[0].hp, s.bases[1].hp), (9, 9))
        self.assertEqual(s.tanks[0].direction, Direction.RIGHT)
        self.assertEqual(s.tanks[1].direction, Direction.LEFT)

    def test_six_actions(self):
        self.assertEqual(len(make(OPEN).legal_actions()), 6)

    def test_max_ply_only_stores_pending(self):
        s = make(OPEN)
        s2 = s.result(Action.MOVE_DOWN)
        self.assertEqual(s2.player(), 1)
        self.assertEqual(s2.pending, Action.MOVE_DOWN)
        self.assertEqual((s2.tanks[0].x, s2.tanks[0].y), (0, 1))
        self.assertEqual(s2.cycle, 0)

    def test_result_does_not_change_original(self):
        s = make(OPEN)
        play(s, Action.MOVE_DOWN, Action.MOVE_DOWN)
        self.assertEqual((s.tanks[0].x, s.tanks[0].y), (0, 1))
        self.assertIsNone(s.pending)


class TestMovement(unittest.TestCase):
    def test_move_one_cell(self):
        s = play(make(OPEN), Action.MOVE_RIGHT, Action.STAY)
        self.assertEqual((s.tanks[0].x, s.tanks[0].y), (1, 1))
        self.assertEqual(s.cycle, 1)

    def test_move_changes_facing_and_stay_keeps_it(self):
        s = play(make(OPEN), Action.MOVE_DOWN, Action.STAY)
        self.assertEqual(s.tanks[0].direction, Direction.DOWN)
        self.assertEqual(s.tanks[1].direction, Direction.LEFT)

    def test_blocked_by_wall_turns_only(self):
        s = play(wall_at(1), Action.MOVE_RIGHT, Action.STAY)
        self.assertEqual((s.tanks[0].x, s.tanks[0].y), (0, 1))
        self.assertEqual(s.tanks[0].direction, Direction.RIGHT)
        s = play(wall_at(1), Action.MOVE_UP, Action.STAY)
        self.assertEqual(s.tanks[0].direction, Direction.UP)

    def test_blocked_by_map_edge(self):
        s = play(make(OPEN), Action.MOVE_LEFT, Action.STAY)
        self.assertEqual((s.tanks[0].x, s.tanks[0].y), (0, 1))
        self.assertEqual(s.tanks[0].direction, Direction.LEFT)

    def test_blocked_by_base(self):
        s = play(make(OPEN), Action.MOVE_UP, Action.STAY)
        self.assertEqual((s.tanks[0].x, s.tanks[0].y), (0, 1))

    def test_same_target_cell_both_stay(self):
        s = make("A..B\n1.2.")
        s = play(s, Action.MOVE_RIGHT, Action.MOVE_LEFT)
        self.assertEqual((s.tanks[0].x, s.tanks[1].x), (0, 2))

    def test_swap_is_blocked(self):
        s = make("A..B\n12..")
        s = play(s, Action.MOVE_RIGHT, Action.MOVE_LEFT)
        self.assertEqual((s.tanks[0].x, s.tanks[1].x), (0, 1))

    def test_move_into_other_tank_is_blocked(self):
        s = make("A..B\n12..")
        s = play(s, Action.MOVE_RIGHT, Action.STAY)
        self.assertEqual((s.tanks[0].x, s.tanks[1].x), (0, 1))


class TestBullets(unittest.TestCase):
    def test_bullet_flies_3_cells_per_cycle(self):
        s = play(make(OPEN), Action.FIRE, Action.STAY)
        self.assertEqual(len(s.bullets), 1)
        self.assertEqual((s.bullets[0].x, s.bullets[0].y), (3, 1))

    def test_bullet_keeps_flying_next_cycle(self):
        s = play(make(OPEN), Action.FIRE, Action.STAY)
        s = play(s, Action.STAY, Action.STAY)
        self.assertEqual((s.bullets[0].x, s.bullets[0].y), (6, 1))

    def test_wall_hit_at_cell_1_2_3(self):
        for x in (1, 2, 3):
            s = play(wall_at(x), Action.FIRE, Action.STAY)
            self.assertEqual(s.walls[(x, 1)], 2, "wall at cell %d" % x)
            self.assertEqual(len(s.bullets), 0)

    def test_wall_destroyed_after_three_hits(self):
        s = wall_at(2)
        for _ in range(3):
            s = play(s, Action.FIRE, Action.STAY)
        self.assertNotIn((2, 1), s.walls)

    def test_bullet_hits_tank(self):
        s = play(make(SMALL), Action.FIRE, Action.STAY)
        self.assertEqual(s.tanks[1].hp, 5)
        self.assertEqual(len(s.bullets), 0)

    def test_bullet_hits_base(self):
        s = play(make(SMALL), Action.STAY, Action.MOVE_UP)
        s = play(s, Action.STAY, Action.FIRE)
        self.assertEqual(s.bases[1].hp, 8)

    def test_bullet_stops_after_first_hit(self):
        s = make("A...B\n1#..2")
        s = play(s, Action.FIRE, Action.STAY)
        self.assertEqual(s.walls[(1, 1)], 2)
        self.assertEqual(s.tanks[1].hp, 6)

    def test_bullet_leaves_map(self):
        s = play(make(SMALL), Action.MOVE_LEFT, Action.STAY)
        s = play(s, Action.FIRE, Action.STAY)
        self.assertEqual(len(s.bullets), 0)
        self.assertEqual((s.tanks[0].hp, s.bases[0].hp), (6, 9))

    def test_only_one_bullet_per_tank(self):
        s = play(make(OPEN), Action.FIRE, Action.STAY)
        s = play(s, Action.FIRE, Action.STAY)
        self.assertEqual(len(s.bullets), 1)

    def test_friendly_fire(self):
        s = play(make(SMALL), Action.MOVE_UP, Action.STAY)
        s = play(s, Action.FIRE, Action.STAY)
        self.assertEqual(s.bases[0].hp, 8)

class TestEndOfGame(unittest.TestCase):
    def test_win_when_enemy_tank_destroyed(self):
        s = make(SMALL)
        s.tanks[1].hp = 0
        self.assertTrue(s.is_terminal())
        self.assertEqual(s.utility(), 1)

    def test_lose_when_own_base_destroyed(self):
        s = make(SMALL)
        s.bases[0].hp = 0
        self.assertTrue(s.is_terminal())
        self.assertEqual(s.utility(), -1)

    def test_both_lose_is_draw(self):
        s = make(SMALL)
        s.tanks[0].hp = 0
        s.bases[1].hp = 0
        self.assertTrue(s.is_terminal())
        self.assertEqual(s.utility(), 0)

    def test_timeout_is_draw(self):
        s = make(SMALL)
        s.cycle = MAX_CYCLES
        self.assertTrue(s.is_terminal())
        self.assertEqual(s.utility(), 0)

    def test_not_terminal_in_middle_of_cycle(self):
        s = make(SMALL)
        s.tanks[1].hp = 0
        self.assertFalse(s.result(Action.STAY).is_terminal())

    def test_full_kill_by_shooting(self):
        s = make(SMALL)
        for _ in range(6):
            s = play(s, Action.FIRE, Action.STAY)
        self.assertTrue(s.is_terminal())
        self.assertEqual(s.utility(), 1)

if __name__ == "__main__":
    unittest.main()
