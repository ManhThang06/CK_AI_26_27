"""Plugin mẫu dùng agent ngẫu nhiên có sẵn, khởi tạo seed để tái lập demo."""

from task2_tank.algorithms.agents import RandomAgent


def create_agent():
    return RandomAgent(seed=42)
