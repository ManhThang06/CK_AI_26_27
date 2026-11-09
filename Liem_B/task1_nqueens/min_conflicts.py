import random
import time


class Board:
    def __init__(self, N, rng=None, state=None):
        self.N = N
        self.rng = rng if rng is not None else random.Random()

        if state is not None:
            self.state = list(state)
        else:
            self.state = [self.rng.randrange(N) for _ in range(N)]

        # 3 mang dem so luong quan hau tren tung hang va 2 duong cheo
        self.row_count = [0] * N
        self.diag1_count = [0] * (2 * N - 1)
        self.diag2_count = [0] * (2 * N - 1)

        for c in range(N):
            r = self.state[c]
            self._add_queen(c, r)

    def _diag1(self, r, c):
        return r - c + self.N - 1

    def _diag2(self, r, c):
        return r + c

    def _add_queen(self, c, r):
        self.row_count[r] += 1
        self.diag1_count[self._diag1(r, c)] += 1
        self.diag2_count[self._diag2(r, c)] += 1

    def _remove_queen(self, c, r):
        self.row_count[r] -= 1
        self.diag1_count[self._diag1(r, c)] -= 1
        self.diag2_count[self._diag2(r, c)] -= 1

    def conflicts_at(self, c, r):
        d1 = self._diag1(r, c)
        d2 = self._diag2(r, c)
        conflicts = self.row_count[r] + self.diag1_count[d1] + self.diag2_count[d2]

        # Neu o (c, r) dang co san quan hau cua cot c thi tru 3
        if self.state[c] == r:
            conflicts -= 3
        return conflicts

    def total_conflicts(self):
        h = 0
        for k in self.row_count:
            h += k * (k - 1) // 2
        for k in self.diag1_count:
            h += k * (k - 1) // 2
        for k in self.diag2_count:
            h += k * (k - 1) // 2
        return h

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
    def __init__(self, N, max_steps=50000, mode="standard", tabu_size=5):
        self.N = N
        self.max_steps = max_steps
        self.mode = mode  # "standard", "max_tabu", hoac "roulette"
        self.tabu_size = tabu_size
        self.tabu_list = []

    def select_variable(self, board, conflicted_cols):
        # 1. Ban chuan Slide 30: chon ngau nhien 1 cot dang bi xung dot
        if self.mode == "standard":
            return board.rng.choice(conflicted_cols)

        # 2. Heuristic 1: Chon cot nhieu xung dot nhat ket hop danh sach Tabu
        if self.mode == "max_tabu":
            valid_cols = [c for c in conflicted_cols if c not in self.tabu_list]
            if not valid_cols:
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

        # 3. Heuristic 2: Chon theo xac suat ty le thuan voi so xung dot (Roulette)
        if self.mode == "roulette":
            weights = [board.conflicts_at(c, board.state[c]) for c in conflicted_cols]
            return board.rng.choices(conflicted_cols, weights=weights, k=1)[0]

        raise ValueError("Che do chon bien khong hop le")

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

        # Pha hoa ngau nhien giua cac hang cung dat xung dot nho nhat
        return board.rng.choice(best_rows)

    def solve(self, initial_state=None, seed=None):
        rng = random.Random(seed) if seed is not None else random.Random()
        board = Board(self.N, rng=rng, state=initial_state)
        self.tabu_list = []

        start_time = time.perf_counter()

        for step in range(self.max_steps):
            conflicted_cols = board.conflicted_columns()

            # Dieu kien dung: khong con cot nao xung dot (h = 0)
            if not conflicted_cols:
                return {
                    "success": True,
                    "solution": list(board.state),
                    "steps": step,
                    "time_sec": time.perf_counter() - start_time,
                }

            col = self.select_variable(board, conflicted_cols)
            best_row = self.select_best_row(board, col)
            board.move_queen(col, best_row)

        # Kiem tra lai sau buoc cuoi cung
        solved = len(board.conflicted_columns()) == 0
        return {
            "success": solved,
            "solution": list(board.state) if solved else None,
            "steps": self.max_steps,
            "time_sec": time.perf_counter() - start_time,
        }
    
def slow_conflicts(state):
    """
    Tinh tong so cap quan hau tan cong nhau.
    Moi cot co mot quan hau.
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