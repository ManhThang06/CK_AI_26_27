import unittest

from task2_tank.algorithms.scenarios import load_state
from task2_tank.engine.constants import Action


class PluginTests(unittest.TestCase):
    def test_example_plugin_is_loaded(self):
        from task2_tank.gui.agent_registry import build_registry
        specs, errors = build_registry()
        self.assertEqual(errors, [])
        plugin = [s for s in specs if s.source == "plugin"]
        self.assertTrue(plugin)
        agent = plugin[0].factory(1)
        self.assertIn(agent.choose_action(load_state("small")), Action)


