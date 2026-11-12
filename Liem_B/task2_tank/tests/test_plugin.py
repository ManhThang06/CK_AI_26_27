import os
import unittest

from CK_AI_26_27.Liem_B.task2_tank.engine import Action
from CK_AI_26_27.Liem_B.task2_tank.plugin_loader import load_agent, AgentLoadError, MAX_STRIKES
from CK_AI_26_27.Liem_B.task2_tank.agents.builtin import ChaserAgent, RandomAgent
from CK_AI_26_27.Liem_B.task2_tank.gui.match import Match

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(BASE, "external_agents")
MAP = os.path.join(BASE, "maps", "small.txt")


class TestPlugin(unittest.TestCase):
    def test_load_external_file(self):
        a = load_agent(os.path.join(EXT, "demo_corner_camper.py"))
        m = Match(MAP, a, load_agent("task2_tank.agents.builtin:ChaserAgent"))
        m.step()
        self.assertEqual(len(m.history), 1)

    def test_crash_agent_does_not_kill_game(self):
        log = []
        bad = load_agent(os.path.join(EXT, "bad_agent_crash.py"), log=log)
        m = Match(MAP, bad, load_agent("task2_tank.agents.builtin:RandomAgent"))
        for _ in range(10):
            m.step()
        self.assertTrue(log)
        self.assertTrue(all(h[2] == "STAY" for h in m.history if h[1] == "MAX"))
        self.assertEqual(bad.strikes, MAX_STRIKES)     # sau 3 loi lien tiep thi khong goi nua

    def test_timeout(self):
        log = []
        slow = load_agent(os.path.join(EXT, "bad_agent_slow.py"), time_limit=0.2, log=log)
        self.assertEqual(slow.choose_action(Match(MAP, None, None).state), Action.STAY)
        self.assertIn("qua gio", log[0])

    def test_bad_files_raise_load_error(self):
        with self.assertRaises(AgentLoadError):
            load_agent(os.path.join(EXT, "khong_ton_tai.py"))
        bad = os.path.join(BASE, "logs", "_syntax_error.py")
        with open(bad, "w") as f:
            f.write("def (:\n")
        try:
            with self.assertRaises(AgentLoadError):
                load_agent(bad)
        finally:
            os.remove(bad)

    def test_full_match_reaches_terminal(self):
        m = Match(MAP, load_agent(os.path.join(EXT, "demo_corner_camper.py")),
                  load_agent("task2_tank.agents.builtin:ChaserAgent"))
        n = 0
        while not m.finished() and n < 1000:
            m.step()
            n += 1
        self.assertTrue(m.finished())
        self.assertIn(m.result_text(), ("Tank 1 (MAX) thang", "Tank 2 (MIN) thang", "Hoa"))


if __name__ == "__main__":
    unittest.main()
