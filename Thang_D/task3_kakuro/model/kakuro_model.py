# Mô hình CSP cho Kakuro (Task 3) - dùng Run / Propagator trong propagation.py
#
# Cách ghi bảng: mỗi ô là một trong
#   "."          ô trắng (biến)
#   "#"          ô đen không có gợi ý
#   (d, a)       ô gợi ý: d = tổng cột bên dưới, a = tổng hàng bên phải (None nếu không có)
from .propagation import Run, Propagator

B = "#"
W = "."

# ---------------------------------------------------------------- bảng mẫu 5x5
EXAMPLE = [
    [B,        B,         (21, None), (14, None), B],
    [B,        (14, 12),  W,         W,         (11, None)],
    [(None, 21), W,       W,         W,         W],
    [(None, 11), W,       W,         W,         W],
    [B,        (None, 16), W,        W,         B],
]

# ---------------------------------------------------------------- bảng test 9x9
TEST = [
    [B,           B,           (44, None),  (16, None),  (9, None),   B,          (15, None),  (44, None),  B],
    [B,           (None, 22),  W,           W,           W,           (11, 3),    W,           W,           (14, None)],
    [B,           (17, 28),    W,           W,           W,           W,          W,           W,           W],
    [(None, 14),  W,           W,           B,           (12, 20),    W,          W,           W,           W],
    [(None, 17),  W,           W,           (29, 22),    W,           W,          W,           W,           (7, None)],
    [B,           (12, 28),    W,           W,           W,           W,          (None, 12),  W,           W],
    [(None, 14),  W,           W,           W,           W,           (7, None),  (12, 6),     W,           W],
    [(None, 39),  W,           W,           W,           W,           W,          W,           W,           B],
    [B,           (None, 16),  W,           W,           (None, 8),   W,          W,           W,           B],
]


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


# ---------------------------------------------------------------- kiểm tra + giải thử
def check_model(grid, runs):
    whites = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == W}
    in_runs = {}
    for run in runs:
        for cell in run.cells:
            in_runs[cell] = in_runs.get(cell, 0) + 1
    assert set(in_runs) == whites, "có ô trắng không thuộc run nào"
    assert all(n == 2 for n in in_runs.values()), "mỗi ô trắng phải thuộc đúng 2 run"
    assert all(len(r.cells) >= 2 for r in runs), "run ngắn hơn 2 ô"
    return len(whites)


def solve(grid, runs):
    """Backtracking + MRV + Degree, forward checking qua Propagator.assign."""
    prop = Propagator(runs)
    dom = prop.initial_domains()
    ok, removed0 = prop.propagate_all(dom)
    stats = {"nodes": 0, "backtracks": 0, "pruned_init": len(removed0)}
    if not ok:
        return None, stats, prop

    def pick():
        free = [c for c in dom if len(dom[c]) > 1]
        if not free:
            return None
        # MRV, hoà thì Degree (số ô chưa gán cùng run)
        def deg(c):
            return sum(1 for run in prop.runs_of[c] for x in run.cells if x != c and len(dom[x]) > 1)
        return min(free, key=lambda c: (len(dom[c]), -deg(c)))

    def rec():
        cell = pick()
        if cell is None:
            return True
        for v in sorted(dom[cell]):       # (LCV có thể thay bước sắp xếp này)
            stats["nodes"] += 1
            ok, removed = prop.assign(dom, cell, v)
            if ok and rec():
                return True
            Propagator.undo(dom, removed)
            stats["backtracks"] += 1
        return False

    found = rec()
    return ({c: next(iter(d)) for c, d in dom.items()} if found else None), stats, prop


def verify(runs, sol):
    for run in runs:
        vals = [sol[c] for c in run.cells]
        if sum(vals) != run.total or len(set(vals)) != len(vals):
            return False, run.name
    return True, None


def show(grid, sol):
    for r, row in enumerate(grid):
        print(" ".join(str(sol[(r, c)]) if x == W else "#" for c, x in enumerate(row)))


if __name__ == "__main__":
    for name, grid in (("EXAMPLE 5x5", EXAMPLE), ("TEST 9x9", TEST)):
        runs = build_runs(grid)
        n = check_model(grid, runs)
        print(f"== {name}: {n} biến, {len(runs)} run "
              f"({sum(r.name[0]=='A' for r in runs)} ngang, {sum(r.name[0]=='D' for r in runs)} dọc)")
        sol, stats, _ = solve(grid, runs)
        print("   stats:", stats)
        if sol:
            print("   verify:", verify(runs, sol))
            show(grid, sol)
        else:
            print("   không tìm được nghiệm")
