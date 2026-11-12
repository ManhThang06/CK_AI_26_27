"""Agent qua cham co y de chung minh timeout hoat dong."""
import time
from CK_AI_26_27.Liem_B.task2_tank.engine import Action
from CK_AI_26_27.Liem_B.task2_tank.agents.base_agent import Agent


class SlowAgent(Agent):
    name = "SlowAgent"

    def choose_action(self, state):
        time.sleep(5)
        return Action.FIRE
