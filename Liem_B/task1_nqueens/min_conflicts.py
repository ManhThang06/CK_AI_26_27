import random
import time

class Board:
    def __init__(self, N, rng=None, state=None):
        if type(N) is not int or N < 1:
            raise ValueError("N phải là số nguyên dương")
        self.N = N
        self.rng = rng if rng is not None else random.Random()

        if state is not None:
            self.state = list(state)
        else:
            self.state = [self.rng.randrange(N) for _ in range(N)]

        if len(self.state) != N or any(type(row) is not int or not 0 <= row < N for row in self.state):
            raise ValueError("Trạng thái phải có đúng N hàng, mỗi hàng thuộc 0 đến N - 1")

        # Ba mảng đếm hậu trên từng hàng và hai hướng đường chéo.
        self.row_count = [0] * N
        self.diag1_count = [0] * (2 * N - 1)
        self.diag2_count = [0] * (2 * N - 1)
        self._conflict_pairs = 0

        for c in range(N):
            r = self.state[c]
            self._add_queen(c, r)

    def _diag1(self, r, c):
        return r - c + self.N - 1

    def _diag2(self, r, c):
        return r + c

    def _add_queen(self, c, r):
        # Mỗi hậu đang có trên hàng hoặc đường chéo tạo thêm một cặp xung đột.
        self._conflict_pairs += (
            self.row_count[r]
            + self.diag1_count[self._diag1(r, c)]
            + self.diag2_count[self._diag2(r, c)]
        )
        self.row_count[r] += 1
        self.diag1_count[self._diag1(r, c)] += 1
        self.diag2_count[self._diag2(r, c)] += 1

    def _remove_queen(self, c, r):
        self.row_count[r] -= 1
        self.diag1_count[self._diag1(r, c)] -= 1
        self.diag2_count[self._diag2(r, c)] -= 1
        self._conflict_pairs -= (
            self.row_count[r]
            + self.diag1_count[self._diag1(r, c)]
            + self.diag2_count[self._diag2(r, c)]
        )

    def conflicts_at(self, c, r):
        d1 = self._diag1(r, c)
        d2 = self._diag2(r, c)
        conflicts = self.row_count[r] + self.diag1_count[d1] + self.diag2_count[d2]

        # Tại hàng hiện tại, trừ chính hậu đang được tính trong cả ba mảng.
        if self.state[c] == r:
            conflicts -= 3
        return conflicts

    def total_conflicts(self):
        """Trả về số cặp xung đột trong O(1), cập nhật khi thêm hoặc bỏ hậu."""
        return self._conflict_pairs

    def conflicted_columns(self):
        result = []
        for c in range(self.N):
            r = self.state[c]
            if self.conflicts_at(c, r) > 0:
                result.append(c)
        return result

    def move_queen(self, c, new_row):
        old_row = self.state[c]
        if old_row == new_row:
            return
        self._remove_queen(c, old_row)
        self.state[c] = new_row
        self._add_queen(c, new_row)


class MinConflictsSolver:
    def __init__(self, N, max_steps=50000, mode="standard", tabu_size=5, restart_after=None):
        if type(N) is not int or N < 1:
            raise ValueError("N phải là số nguyên dương")
        if type(max_steps) is not int or max_steps < 0:
            raise ValueError("Số bước tối đa phải là số nguyên không âm")
        if mode not in ("standard", "max_tabu", "roulette"):
            raise ValueError("Chế độ chọn biến không hợp lệ")
        if type(tabu_size) is not int or tabu_size < 0:
            raise ValueError("Độ dài tabu phải là số nguyên không âm")
        if restart_after is not None and (type(restart_after) is not int or restart_after < 1):
            raise ValueError("Ngưỡng khởi động lại phải là số nguyên dương hoặc None")
        self.N = N
        # Khởi động lại sau K bước không cải thiện kỷ lục của lần khởi động hiện tại.
        # Mặc định None để dùng Min-Conflicts chuẩn theo Lecture 08.
        self.restart_after = restart_after
        self.max_steps = max_steps
        self.mode = mode
        self.tabu_size = tabu_size
        self.tabu_list = []

    def select_variable(self, board, conflicted_cols):
        # Lecture 08, trang 30 chọn ngẫu nhiên một biến đang xung đột.
        if self.mode == "standard":
            return board.rng.choice(conflicted_cols)

        # Ưu tiên cột nhiều xung đột, hạn chế chọn lại các cột gần đây.
        if self.mode == "max_tabu":
            valid_cols = [c for c in conflicted_cols if c not in self.tabu_list]
            if not valid_cols:
                # Nới điều kiện tabu nếu mọi cột xung đột đều đang bị hạn chế.
                valid_cols = conflicted_cols

            max_c = -1
            best_cols = []
            for c in valid_cols:
                c_val = board.conflicts_at(c, board.state[c])
                if c_val > max_c:
                    max_c = c_val
                    best_cols = [c]
                elif c_val == max_c:
                    best_cols.append(c)

            chosen = board.rng.choice(best_cols)
            self.tabu_list.append(chosen)
            if len(self.tabu_list) > self.tabu_size:
                self.tabu_list.pop(0)
            return chosen

        # Chọn biến theo xác suất tỷ lệ với số xung đột của biến đó.
        if self.mode == "roulette":
            weights = [board.conflicts_at(c, board.state[c]) for c in conflicted_cols]
            return board.rng.choices(conflicted_cols, weights=weights, k=1)[0]

        raise ValueError("Chế độ chọn biến không hợp lệ")

    def select_best_row(self, board, col):
        min_c = self.N + 1
        best_rows = []

        for r in range(self.N):
            c_val = board.conflicts_at(col, r)
            if c_val < min_c:
                min_c = c_val
                best_rows = [r]
            elif c_val == min_c:
                best_rows.append(r)

        # Phá hòa ngẫu nhiên giữa các hàng có số xung đột nhỏ nhất.
        return board.rng.choice(best_rows)

    def solve(self, initial_state=None, seed=None):
        start_time = time.perf_counter()
        rng = random.Random(seed) if seed is not None else random.Random()
        board = Board(self.N, rng=rng, state=initial_state)
        self.tabu_list = []

        best_h = board.total_conflicts()
        since_best = 0
        restarts = 0

        for step in range(self.max_steps):
            conflicted_cols = board.conflicted_columns()

            # Dừng khi không còn cột nào xung đột.
            if not conflicted_cols:
                return {
                    "success": True,
                    "solution": list(board.state),
                    "steps": step,
                    "restarts": restarts,
                    "time_sec": time.perf_counter() - start_time,
                }

            col = self.select_variable(board, conflicted_cols)
            best_row = self.select_best_row(board, col)
            board.move_queen(col, best_row)

            if self.restart_after is not None:
                h = board.total_conflicts()
                if h < best_h:
                    best_h, since_best = h, 0
                else:
                    since_best += 1
                if since_best >= self.restart_after:
                    board = Board(self.N, rng=rng)
                    self.tabu_list = []
                    best_h, since_best = board.total_conflicts(), 0
                    restarts += 1

        # Kiểm tra cả nghiệm xuất hiện sau bước cuối được phép.
        solved = len(board.conflicted_columns()) == 0
        return {
            "success": solved,
            "solution": list(board.state) if solved else None,
            "steps": self.max_steps,
            "restarts": restarts,
            "time_sec": time.perf_counter() - start_time,
        }
    
def slow_conflicts(state):
    """
    Đếm số cặp hậu tấn công nhau bằng cách duyệt từng cặp trong O(N²).
    Mỗi cột có một hậu, state[c] là hàng của hậu ở cột c.
    Dùng để kiểm tra độc lập bộ đếm nhanh của Board.
    """
    N = len(state)
    conflicts = 0
    for c1 in range(N):
        for c2 in range(c1 + 1, N):
            r1 = state[c1]
            r2 = state[c2]
            if r1 == r2 or abs(r1 - r2) == abs(c1 - c2):
                conflicts += 1
    return conflicts


if __name__ == "__main__":
    for mode in ["standard", "max_tabu", "roulette"]:
        solver = MinConflictsSolver(N=50, max_steps=10000, mode=mode, tabu_size=5)
        res = solver.solve(seed=42)
        print(f"Mode: {mode:10s} | Solved: {res['success']} | Steps: {res['steps']:4d} | Time: {res['time_sec']*1000:.2f} ms")
