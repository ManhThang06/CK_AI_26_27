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
    """Kiem tra bang. Tra ve list canh bao (chuoi); rong nghia la bang hop le chuan.

    Loi nang (bang khong the dua vao CSP) -> ValueError:
      - o trang khong thuoc run nao (khong co goi y ngang lan doc).
    Canh bao (van giai duoc, solver se tu ket luan vo nghiem neu can):
      - o trang chi thuoc 1 run, run chi co 1 o,
      - run co tong khong the dat duoc bang cac chu so khac nhau tu 1 den 9.
    """
    whites = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == W}
    in_runs = {}
    for run in runs:
        for cell in run.cells:
            in_runs[cell] = in_runs.get(cell, 0) + 1
    orphans = sorted(whites - set(in_runs))
    if orphans:
        raise ValueError(f"o trang khong thuoc run nao: {orphans[:5]}")

    warnings = []
    single = sorted(c for c, n in in_runs.items() if n != 2)
    if single:
        warnings.append(f"{len(single)} o trang chi thuoc 1 run, vi du {single[:3]}")
    short = [run.name for run in runs if len(run.cells) < 2]
    if short:
        warnings.append(f"{len(short)} run chi co 1 o: {', '.join(short[:6])}")
    impossible = []
    for run in runs:
        k = len(run.cells)
        if k > 9 or not (k * (k + 1) // 2 <= run.total <= sum(range(10 - k, 10))):
            impossible.append(f"{run.name}(k={k},sum={run.total})")
    if impossible:
        warnings.append(f"{len(impossible)} run co tong khong the dat duoc "
                        f"(vo nghiem): {', '.join(impossible[:6])}")
    return warnings
