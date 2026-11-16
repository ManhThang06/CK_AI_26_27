from abc import ABC, abstractmethod
from .board import Board


class NQueensSolver(ABC):
    """Lớp cha trừu tượng của mọi solver N-quân hậu.

    `solve()` là template method: xác định N, gọi `_solve()` của lớp con,
    rồi kiểm tra độc lập nghiệm bằng `Board.is_valid()`.
    Kết quả là dict, luôn có khóa "solution" (columns[row] = col hoặc None).
    """

    def __init__(self, n=None):
        if n is not None and (type(n) is not int or n < 1):
            raise ValueError("N phải là số nguyên dương")
        self.n = n

    def solve(self, n=None, **options):
        n = self.n if n is None else n
        if type(n) is not int or n < 1:
            raise ValueError("N phải là số nguyên dương")
        result = self._solve(n, **options)
        solution = result.get("solution")
        if solution is not None and not Board(solution).is_valid():
            raise RuntimeError("Solution failed independent validation")
        return result

    @abstractmethod
    def _solve(self, n, **options):
        """Giải bài toán với kích thước n, trả về dict kết quả."""
