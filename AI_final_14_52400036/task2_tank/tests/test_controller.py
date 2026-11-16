import unittest

from task2_tank.algorithms.agents import RandomAgent, play_match
from task2_tank.algorithms.scenarios import load_state
from task2_tank.engine import Action
from task2_tank.engine.match import MatchSession, SafeAgent
from task2_tank.gui.game_controller import GameController


class ControllerTests(unittest.TestCase):
    def test_safe_agent_preserves_state_and_handles_invalid_output(self):
        class InvalidAgent:
            def choose_action(self, state):
                state.tanks[0].hp = 0
                return "FIRE"
        state = load_state("small")
        agent = SafeAgent(InvalidAgent())
        self.assertEqual(agent.choose_action(state), Action.STAY)
        self.assertEqual(state.tanks[0].hp, 6)
        self.assertIn("ValueError", agent.last_error)
        self.assertEqual(agent.moves, 1)

    def test_safe_agent_handles_exception(self):
        class BrokenAgent:
            def choose_action(self, state):
                raise RuntimeError("lỗi thử nghiệm")
        agent = SafeAgent(BrokenAgent())
        self.assertEqual(agent.choose_action(load_state("small")), Action.STAY)
        self.assertIn("RuntimeError", agent.last_error)

    def test_controller_reset_restores_state_and_agents(self):
        controller = GameController("small", [RandomAgent, RandomAgent], ["A", "B"])
        controller.apply(Action.STAY)
        controller.apply(Action.STAY)
        self.assertEqual(controller.state.cycle, 1)
        self.assertEqual(len(controller.log), 1)
        controller.reset()
        self.assertEqual(controller.state.cycle, 0)
        self.assertIsNone(controller.state.pending)
        self.assertEqual(len(controller.log), 0)

    def test_session_demo_and_controller_share_result(self):
        state = load_state("small")
        state.cycle = 98
        match = MatchSession(state, [RandomAgent(1), RandomAgent(2)])
        final = match.run()
        demo, utility, _, _ = play_match(state, RandomAgent(1), RandomAgent(2))
        self.assertEqual(final.utility(), utility)
        self.assertEqual(final.cycle, demo.cycle)
        self.assertEqual(match.agents[0].moves, 2)
        self.assertEqual(state.cycle, 98)

    def test_terminal_state_is_unchanged(self):
        state = load_state("small")
        state.tanks[0].hp = 0
        match = MatchSession(state, [RandomAgent(), RandomAgent()])
        match.apply(Action.FIRE)
        self.assertEqual(match.state.cycle, state.cycle)
        self.assertIsNone(match.state.pending)
