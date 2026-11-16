"""Agent mẫu để nạp vào GUI: chọn hành động ngẫu nhiên.

Một plugin cần có hàm create_agent() trả về đối tượng agent, hoặc một lớp có
phương thức choose_action(state). Xem README.md mục "Nạp thuật toán của nhóm khác".
"""

import random


class RandomAgent:
    name = "Random"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def choose_action(self, state):
        # state.player() cho biết đang chơi bên nào (0 = P1, 1 = P2); agent phải chơi được cả hai bên.
        return self.rng.choice(state.legal_actions())


def create_agent():
    return RandomAgent()
