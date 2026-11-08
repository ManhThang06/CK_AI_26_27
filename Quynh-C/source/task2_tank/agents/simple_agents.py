import random

from .base_agent import Agent


class RandomAgent(Agent):
    name = "random"

    def __init__(self, seed=0):
        super().__init__()
        self.rng = random.Random(seed)

    def choose_action(self, state):
        return self.rng.choice(state.legal_actions())
