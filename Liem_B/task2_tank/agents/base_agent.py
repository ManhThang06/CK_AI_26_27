class Agent:
    """Interface every tank agent follows (also used for agents loaded from other groups).

    choose_action(state) gets a GameState in which it is this agent's turn
    (state.player() tells which side) and returns one Action.
    """
    name = "agent"

    def __init__(self):
        self.nodes = 0          # states visited in the last search
        self.last_depth = 0     # depth (in plies) reached in the last search

    def reset_stats(self):
        self.nodes = 0
        self.last_depth = 0

    def choose_action(self, state):
        raise NotImplementedError
