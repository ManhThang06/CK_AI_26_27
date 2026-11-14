class Board:

    def __init__(self, columns):
        self.columns = list(columns)

    def is_valid(self):
        n = len(self.columns)
        if not n or any(type(c) is not int or not 0 <= c < n for c in self.columns):
            return False
        for row in range(n):
            for other in range(row):
                if (self.columns[row] == self.columns[other]
                        or abs(self.columns[row] - self.columns[other]) == row - other):
                    return False
        return True

    def __str__(self):
        n = len(self.columns)
        return "\n".join(" ".join("Q" if c == col else "." for c in range(n))
                         for col in self.columns)