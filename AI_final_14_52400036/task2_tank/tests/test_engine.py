import unittest

from task2_tank.algorithms.scenarios import load_state
from task2_tank.engine.constants import Action


class EngineTests(unittest.TestCase):
    def test_initial_hp_matches_spec(self):
        st = load_state("small")
        self.assertEqual([t.hp for t in st.tanks], [6, 6])
        self.assertEqual([b.hp for b in st.bases], [9, 9])
        self.assertTrue(all(hp == 3 for hp in st.walls.values()))

    def test_six_actions(self):
        self.assertEqual(len(load_state("small").legal_actions()), 6)

    def test_bullet_moves_three_cells_per_cycle(self):
        from task2_tank.engine import GameMap, GameState
        st = GameState.from_map(GameMap.parse("1.......2\nA.......B"))
        st = st.result(Action.FIRE).result(Action.STAY)
        self.assertEqual((st.bullets[0].x, st.bullets[0].y), (3, 0))

    def test_bullet_damages_and_stops_at_tank(self):
        from task2_tank.engine import GameMap, GameState
        st = GameState.from_map(GameMap.parse("12\nAB"))
        st = st.result(Action.FIRE).result(Action.STAY)
        self.assertEqual(st.tanks[1].hp, 5)
        self.assertEqual(st.bullets, [])



class TerminalRegressionTests(unittest.TestCase):
    def test_destroyed_tank_does_not_fire(self):
        from task2_tank.engine import GameMap, GameState, Bullet, Direction
        state = GameState.from_map(GameMap.parse("1...2\nA...B"))
        state.tanks[0].hp = 1
        state.bullets = [Bullet(0, 0, Direction.LEFT, 1)]
        final = state.result(Action.FIRE).result(Action.STAY)
        self.assertEqual(final.tanks[0].hp, 0)
        self.assertFalse(any(b.owner == 0 for b in final.bullets))
        self.assertTrue(final.is_terminal())
        self.assertEqual(final.utility(), -1)

    def test_wall_collision_at_each_substep(self):
        from task2_tank.engine import GameMap, GameState
        for distance in (1, 2, 3):
            state = GameState.from_map(GameMap.parse("1....2\nA....B"))
            state.walls[(distance, 0)] = 3
            final = state.result(Action.FIRE).result(Action.STAY)
            self.assertEqual(final.walls[(distance, 0)], 2)
            self.assertEqual(final.bullets, [])
