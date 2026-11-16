from abc import ABC, abstractmethod


class VariableSelector(ABC):
    """Chiến lược chọn biến (một hàng đang xung đột) cho Min-Conflicts."""

    name = ""

    def reset(self):
        """Xóa trạng thái nội bộ; gọi khi bắt đầu lần chạy mới hoặc restart."""

    @abstractmethod
    def select(self, board, conflicted):
        """Trả về một hàng trong danh sách `conflicted`."""


class StandardSelector(VariableSelector):
    """Min-Conflicts chuẩn: chọn ngẫu nhiên một hàng đang xung đột."""

    name = "standard"

    def select(self, board, conflicted):
        return board.rng.choice(conflicted)


class MaxTabuSelector(VariableSelector):
    """Heuristic đề xuất: hàng xung đột nhiều nhất, bỏ qua các hàng vừa chọn (tabu list)."""

    name = "max_tabu"

    def __init__(self, tabu_size=5):
        if type(tabu_size) is not int or tabu_size < 0:
            raise ValueError("Độ dài tabu phải là số nguyên không âm")
        self.tabu_size = tabu_size
        self.tabu_list = []

    def reset(self):
        self.tabu_list = []

    def select(self, board, conflicted):
        candidates = [r for r in conflicted if r not in self.tabu_list]
        if not candidates:
            candidates = conflicted

        max_value = -1
        best = []
        for r in candidates:
            value = board.conflicts_at(r, board.columns[r])
            if value > max_value:
                max_value = value
                best = [r]
            elif value == max_value:
                best.append(r)

        chosen = board.rng.choice(best)
        self.tabu_list.append(chosen)
        if len(self.tabu_list) > self.tabu_size:
            self.tabu_list.pop(0)
        return chosen


class RouletteSelector(VariableSelector):
    """Chọn ngẫu nhiên có trọng số bằng số xung đột của từng hàng."""

    name = "roulette"

    def select(self, board, conflicted):
        weights = [board.conflicts_at(r, board.columns[r]) for r in conflicted]
        return board.rng.choices(conflicted, weights=weights, k=1)[0]


SELECTORS = {cls.name: cls for cls in (StandardSelector, MaxTabuSelector, RouletteSelector)}


def make_selector(mode, tabu_size=5):
    """Tạo selector từ tên chế độ ("standard", "max_tabu", "roulette")."""
    if mode not in SELECTORS:
        raise ValueError("Chế độ chọn biến không hợp lệ")
    if mode == MaxTabuSelector.name:
        return MaxTabuSelector(tabu_size)
    return SELECTORS[mode]()
