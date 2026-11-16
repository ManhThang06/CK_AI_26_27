"""Thí nghiệm so sánh 4 cấu hình tìm kiếm: Minimax, Alpha-Beta, Heuristic Minimax,
Heuristic Minimax + Alpha-Beta.

Cùng điều kiện cho mọi cấu hình:
  - cùng tập trạng thái xuất phát (ba map, mỗi map có trạng thái đầu ván và các trạng thái
    giữa ván tạo bằng warmup() với seed cố định), HP chuẩn 6/9/3 của đề;
  - cùng độ sâu (số cycle nhìn trước), mỗi cycle gồm 2 ply;
  - tất định: tắt move ordering, tắt lọc nước vô tác dụng, tắt nhiễu và chọn ngẫu nhiên.
Minimax và Alpha-Beta giới hạn độ sâu thì tính giá trị bằng chênh lệch HP
(horizon_score); hai bản Heuristic dùng hàm đánh giá Eval() đầy đủ.

Chạy (từ thư mục chứa task2_tank):
    python -m task2_tank.experiments.compare_search
    python -m task2_tank.experiments.compare_search --max-depth 3 --out task2_tank/experiments/results
"""

import argparse
import csv
import math
import os
import json
import platform
import time
from collections import defaultdict

from ..algorithms.adversarial import MinimaxSearch, AlphaBetaSearch
from ..algorithms.heuristic_search import HeuristicMinimaxSearch, HeuristicAlphaBetaSearch
from ..algorithms.scenarios import load_state, warmup
from ..algorithms.heuristic_eval import _plan

MAPS = ("small", "medium", "full")
WARMUPS = ((0, 0), (4, 1), (8, 2), (12, 3))   # (số cycle chơi ngẫu nhiên, seed)


def _heuristic(cls, depth):
    return cls(depth=depth, move_ordering=False, prune_noop=False, avoid_doomed=False)


CONFIGS = {
    "Minimax": lambda d: MinimaxSearch(horizon=d, horizon_score=True),
    "Alpha-Beta": lambda d: AlphaBetaSearch(horizon=d, horizon_score=True),
    "Heuristic Minimax": lambda d: _heuristic(HeuristicMinimaxSearch, d),
    "Heuristic Alpha-Beta": lambda d: _heuristic(HeuristicAlphaBetaSearch, d),
}
# cặp phải cho cùng giá trị gốc: cắt tỉa không được đổi kết quả
EQUIVALENT = (("Minimax", "Alpha-Beta"), ("Heuristic Minimax", "Heuristic Alpha-Beta"))

FIELDS = ["map", "warmup", "depth", "algorithm", "time_s", "nodes_generated", "nodes_expanded",
          "terminal_nodes", "cutoff_nodes", "heuristic_evals", "cutoffs", "pruned_branches", "max_depth_ply",
          "root_value", "action"]


def scenarios():
    for m in MAPS:
        base = load_state(m)
        for cycles, seed in WARMUPS:
            yield m, "c%d-s%d" % (cycles, seed), warmup(base, cycles, seed)


def run(max_depth, repeats):
    rows = []
    for m, tag, state in scenarios():
        for d in range(1, max_depth + 1):
            for name, make in CONFIGS.items():
                best = None
                for _ in range(repeats):                  # lấy thời gian nhỏ nhất để giảm nhiễu đo
                    _plan.cache_clear()
                    t0 = time.perf_counter()
                    res = make(d).search(state)
                    dt = time.perf_counter() - t0
                    if best is None or dt < best:
                        best = dt
                s = res.stats
                rows.append(dict(
                    map=m, warmup=tag, depth=d, algorithm=name, time_s=round(best, 5),
                    nodes_generated=s.nodes_generated, nodes_expanded=s.nodes_expanded,
                    terminal_nodes=s.terminal_nodes, cutoff_nodes=s.cutoff_nodes, heuristic_evals=getattr(s, "heuristic_evals", 0),
                    cutoffs=s.cutoffs, pruned_branches=s.pruned_branches, max_depth_ply=s.max_depth,
                    root_value=round(res.value, 6), action=res.action.name))
        print("done", m, tag, flush=True)
    return rows


def check_equivalence(rows):
    """Minimax và Alpha-Beta (cùng loại) phải cho cùng giá trị gốc ở mọi kịch bản."""
    idx = {(r["map"], r["warmup"], r["depth"], r["algorithm"]): r for r in rows}
    bad = 0
    for (m, w, d, a), r in idx.items():
        for full, pruned in EQUIVALENT:
            if a == full and not math.isclose(r["root_value"], idx[(m, w, d, pruned)]["root_value"],
                                              abs_tol=1e-6):
                bad += 1
    return bad


def summarize(rows):
    """Trung bình theo (độ sâu, thuật toán) trên toàn bộ kịch bản."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["depth"], r["algorithm"])].append(r)
    out = []
    for (d, a), rs in sorted(groups.items()):
        n = len(rs)
        out.append(dict(
            depth=d, algorithm=a, scenarios=n,
            avg_time_s=sum(x["time_s"] for x in rs) / n,
            avg_nodes=sum(x["nodes_generated"] for x in rs) / n,
            avg_cutoffs=sum(x["cutoffs"] for x in rs) / n,
            avg_pruned=sum(x["pruned_branches"] for x in rs) / n,
            avg_evals=sum(x["heuristic_evals"] for x in rs) / n))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=3, help="số cycle nhìn trước lớn nhất (1-3 là hợp lý)")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args()

    if args.max_depth < 1 or args.repeats < 1:
        ap.error("Độ sâu và số lần chạy phải dương")
    rows = run(args.max_depth, args.repeats)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "compare_search_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)

    with open(os.path.join(args.out, "environment.json"), "w", encoding="utf-8") as f:
        json.dump({"python": platform.python_version(), "platform": platform.platform(),
                   "repeats": args.repeats, "depth": args.max_depth,
                   "timing": "minimum of repeats; cold path cache per search"}, f, indent=2)

    summ = summarize(rows)
    with open(os.path.join(args.out, "compare_search_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)

    print("\n%-5s %-22s %10s %12s %10s %10s %8s" % ("depth", "algorithm", "time (s)", "nodes", "cutoffs",
                                                    "pruned", "evals"))
    for r in summ:
        print("%-5d %-22s %10.4f %12.0f %10.0f %10.0f %8.0f" % (
            r["depth"], r["algorithm"], r["avg_time_s"], r["avg_nodes"], r["avg_cutoffs"],
            r["avg_pruned"], r["avg_evals"]))
    bad = check_equivalence(rows)
    print("\nKiểm tra Alpha-Beta == Minimax (cùng giá trị gốc): %s" %
          ("ĐẠT" if bad == 0 else "LỆCH %d kịch bản" % bad))
    print("Kết quả lưu trong:", args.out)


if __name__ == "__main__":
    main()
