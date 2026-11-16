class Board:
    """Bàn cờ N x N, biểu diễn columns[row] = col (mỗi hàng đúng một quân hậu).

    Là lớp cha dùng chung: SATSolver dùng trực tiếp để kiểm tra nghiệm,
    ConflictBoard (Min-Conflicts) kế thừa để thêm phần đếm xung đột nhanh.
    """

    def __init__(self, columns):
        self.columns = list(columns)

    @property
    def n(self):
        return len(self.columns)

    def count_conflicts(self):
        """Đếm số cặp hậu ăn nhau bằng cách duyệt O(N^2); dùng để kiểm tra độc lập."""
        count = 0
        for row in range(self.n):
            for other in range(row):
                if (self.columns[row] == self.columns[other]
                        or abs(self.columns[row] - self.columns[other]) == row - other):
                    count += 1
        return count

    def is_valid(self):
        n = self.n
        if not n or any(type(c) is not int or not 0 <= c < n for c in self.columns):
            return False
        return self.count_conflicts() == 0

    def __str__(self):
        n = self.n
        return "\n".join(" ".join("Q" if c == col else "." for c in range(n))
                         for col in self.columns)
