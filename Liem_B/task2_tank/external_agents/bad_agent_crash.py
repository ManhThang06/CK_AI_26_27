"""Agent loi co y de chung minh game khong sap."""
from CK_AI_26_27.Liem_B.task2_tank.agents.base_agent import Agent


class CrashAgent(Agent):
    name = "CrashAgent"

    def choose_action(self, state):
        raise RuntimeError("co y gay loi")
