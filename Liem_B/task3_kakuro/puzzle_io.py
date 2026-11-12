"""Doc file de Kakuro JSON (dinh dang cua A/D) thanh (white_cells, clues) cho KakuroChecker.

grid: "#" o den, "." o trang, "d14/a12" o clue (d = tong cot ben duoi, a = tong hang ben phai).
"""
import json


def load_puzzle(path):
    with open(path, encoding="utf-8") as f:
        grid = json.load(f)["grid"]
    R, C = len(grid), len(grid[0])
    white = [(r, c) for r in range(R) for c in range(C) if grid[r][c] == "."]
    clues = []
    for r in range(R):
        for c in range(C):
            tok = grid[r][c]
            if tok in ("#", "."):
                continue
            for part in tok.split("/"):
                kind, target = part[0], int(part[1:])
                dr, dc = (0, 1) if kind == "a" else (1, 0)
                cells, rr, cc = [], r + dr, c + dc
                while 0 <= rr < R and 0 <= cc < C and grid[rr][cc] == ".":
                    cells.append((rr, cc))
                    rr, cc = rr + dr, cc + dc
                clues.append((target, cells))
    return white, clues
