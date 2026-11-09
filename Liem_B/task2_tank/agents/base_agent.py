VALID_ACTIONS = ("MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT", "FIRE", "STAY")


class BaseAgent:
    def __init__(self, player_id, name="BaseAgent"):
        self.player_id = player_id
        self.name = name

    def get_action(self, state):
        """
        Nhan vao ban sao an toan (state.clone()) cua GameState hien tai.
        Tra ve 1 trong 6 chuoi hanh dong hop le trong VALID_ACTIONS.
        """
        return "STAY"