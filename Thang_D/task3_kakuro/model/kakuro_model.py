# Mô hình CSP cho Kakuro (Task 3): dựng các Run (Sum + Alldiff) từ bảng ô.
#
# Cách ghi bảng: mỗi ô là một trong
#   "."          ô trắng (biến)
#   "#"          ô đen không có gợi ý
#   (d, a)       ô gợi ý: d = tổng cột bên dưới, a = tổng hàng bên phải (None nếu không có)
from .propagation import Run

B = "#"
W = "."


def is_white(grid, r, c):
    return 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == W


def build_runs(grid):
    """Quét bảng, mỗi gợi ý ngang/dọc sinh ra một Run (= 1 ràng buộc Sum + Alldiff)."""
    runs, na, nd = [], 0, 0
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if not isinstance(cell, tuple):
                continue
            down, across = cell
            if across is not None:
                cells, cc = [], c + 1
                while is_white(grid, r, cc):
                    cells.append((r, cc)); cc += 1
                na += 1
                runs.append(Run(f"A{na}", cells, across))
            if down is not None:
                cells, rr = [], r + 1
                while is_white(grid, rr, c):
                    cells.append((rr, c)); rr += 1
                nd += 1
                runs.append(Run(f"D{nd}", cells, down))
    return runs


def check_model(grid, runs):
    """Kiểm tra bảng hợp lệ, trả về số biến (ô trắng)."""
    whites = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == W}
    in_runs = {}
    for run in runs:
        for cell in run.cells:
            in_runs[cell] = in_runs.get(cell, 0) + 1
    assert set(in_runs) == whites, "có ô trắng không thuộc run nào"
    assert all(n == 2 for n in in_runs.values()), "mỗi ô trắng phải thuộc đúng 2 run"
    assert all(len(r.cells) >= 2 for r in runs), "run ngắn hơn 2 ô"
    return len(whites)
