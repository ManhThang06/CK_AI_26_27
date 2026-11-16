import random
import time
from .board import Board
from .nqueens_solver import NQueensSolver
from .variable_selectors import make_selector


class ConflictBoard(Board):

    def __init__(self, n, rng=None, columns=None):
        if type(n) is not int or n < 1:
            raise ValueError("N phải là số nguyên dương")
        self.rng = rng if rng is not None else random.Random()
        if columns is None:
            columns = [self.rng.randrange(n) for _ in range(n)]
        super().__init__(columns)
        if len(self.columns) != n or any(type(c) is not int or not 0 <= c < n for c in self.columns):
            raise ValueError("Trạng thái phải có đúng N hàng, mỗi cột thuộc 0 đến N - 1")

        self.col_count = [0] * n
        self.diag1_count = [0] * (2 * n - 1)
        self.diag2_count = [0] * (2 * n - 1)
        self._conflict_pairs = 0
        for row, col in enumerate(self.columns):
            self._add_queen(row, col)

    def _diag1(self, row, col):
        return row - col + self.n - 1

    def _diag2(self, row, col):
        return row + col

    def _add_queen(self, row, col):
        self._conflict_pairs += (self.col_count[col]
                                 + self.diag1_count[self._diag1(row, col)]
                                 + self.diag2_count[self._diag2(row, col)])
        self.col_count[col] += 1
        self.diag1_count[self._diag1(row, col)] += 1
        self.diag2_count[self._diag2(row, col)] += 1

    def _remove_queen(self, row, col):
        self.col_count[col] -= 1
        self.diag1_count[self._diag1(row, col)] -= 1
        self.diag2_count[self._diag2(row, col)] -= 1
        self._conflict_pairs -= (self.col_count[col]
                                 + self.diag1_count[self._diag1(row, col)]
                                 + self.diag2_count[self._diag2(row, col)])

    def conflicts_at(self, row, col):
        conflicts = (self.col_count[col]
                     + self.diag1_count[self._diag1(row, col)]
                     + self.diag2_count[self._diag2(row, col)])
        if self.columns[row] == col:
            conflicts -= 3
        return conflicts

    def total_conflicts(self):
        return self._conflict_pairs

    def conflicted_rows(self):
        return [r for r in range(self.n) if self.conflicts_at(r, self.columns[r]) > 0]

    def best_column(self, row):
        min_value = self.n + 1
        best = []
        for col in range(self.n):
            value = self.conflicts_at(row, col)
            if value < min_value:
                min_value = value
                best = [col]
            elif value == min_value:
                best.append(col)
        return self.rng.choice(best)

    def move_queen(self, row, new_col):
        old_col = self.columns[row]
        if old_col == new_col:
            return
        self._remove_queen(row, old_col)
        self.columns[row] = new_col
        self._add_queen(row, new_col)


class MinConflictsSolver(NQueensSolver):

    def __init__(self, N, max_steps=50000, mode="standard", tabu_size=5,
                 restart_after=None, selector=None):
        super().__init__(N)
        if type(max_steps) is not int or max_steps < 0:
            raise ValueError("Số bước tối đa phải là số nguyên không âm")
        if type(tabu_size) is not int or tabu_size < 0:
            raise ValueError("Độ dài tabu phải là số nguyên không âm")
        if restart_after is not None and (type(restart_after) is not int or restart_after < 1):
            raise ValueError("Ngưỡng khởi động lại phải là số nguyên dương hoặc None")
        self.max_steps = max_steps
        self.restart_after = restart_after
        self.selector = selector if selector is not None else make_selector(mode, tabu_size)

    @property
    def mode(self):
        return self.selector.name

    def _solve(self, n, initial_state=None, seed=None):
        start_time = time.perf_counter()
        rng = random.Random(seed) if seed is not None else random.Random()
        board = ConflictBoard(n, rng=rng, columns=initial_state)
        self.selector.reset()

        best_h = board.total_conflicts()
        since_best = 0
        restarts = 0

        for step in range(self.max_steps):
            conflicted = board.conflicted_rows()
            if not conflicted:
                return self._result(True, board, step, restarts, start_time)

            row = self.selector.select(board, conflicted)
            board.move_queen(row, board.best_column(row))

            if self.restart_after is not None:
                h = board.total_conflicts()
                if h < best_h:
                    best_h, since_best = h, 0
                else:
                    since_best += 1
                if since_best >= self.restart_after:
                    board = ConflictBoard(n, rng=rng)
                    self.selector.reset()
                    best_h, since_best = board.total_conflicts(), 0
                    restarts += 1

        solved = not board.conflicted_rows()
        return self._result(solved, board, self.max_steps, restarts, start_time)

    @staticmethod
    def _result(success, board, steps, restarts, start_time):
        return {
            "success": success,
            "solution": list(board.columns) if success else None,
            "steps": steps,
            "restarts": restarts,
            "time_sec": time.perf_counter() - start_time,
        }

