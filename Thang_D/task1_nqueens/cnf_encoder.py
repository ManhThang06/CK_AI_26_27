from itertools import combinations

class CNFEncoder:

    def __init__(self, n):
        if type(n) is not int or n < 1:
            raise ValueError("N must be a positive integer")
        self.n = n

    def variable(self, row, col):
        return row * self.n + col + 1

    def encode(self):
        n = self.n
        clauses = []
        groups = []
        for row in range(n):
            cells = [self.variable(row, col) for col in range(n)]
            clauses.append(cells)  # Ít nhất một quân hậu trên mỗi hàng.
            groups.append(cells)
        for col in range(n):
            groups.append([self.variable(row, col) for row in range(n)])
        for diagonal in range(1 - n, n):
            groups.append([self.variable(row, row - diagonal) for row in range(n)
                           if 0 <= row - diagonal < n])
        for diagonal in range(2 * n - 1):
            groups.append([self.variable(row, diagonal - row) for row in range(n)
                           if 0 <= diagonal - row < n])
        for cells in groups:
            for first, second in combinations(cells, 2):
                clauses.append([-first, -second])
        return clauses