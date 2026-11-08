"""So sánh Minimax và Alpha-Beta trên cùng các kịch bản (requirement 2).

Chạy từ thư mục chứa task2_tank:
    python -m task2_tank.experiments.compare_search
    python -m task2_tank.experiments.compare_search --max-horizon 6 --minimax-max-horizon 3 --csv results.csv

Mỗi kịch bản là một trạng thái xuất phát cố định (bản đồ của engine, HP chỉnh theo kịch bản,
vài cycle đầu chơi ngẫu nhiên có seed), nên mọi thuật toán nhận đúng cùng dữ liệu vào.
"""

import argparse
import csv

from ..algorithms import MinimaxSearch, AlphaBetaSearch
from ..algorithms.scenarios import load_state, set_hp, warmup

# (tên, bản đồ, HP, số cycle khởi động ngẫu nhiên, seed)
SCENARIOS = [
    ("small-hp-chuan", "small", dict(), 0, 0),
    ("small-hp-thap", "small", dict(tank_hp=1, base_hp=1, wall_hp=1), 3, 1),
    ("small-hp-thap-2", "small", dict(tank_hp=2, base_hp=2, wall_hp=2), 4, 2),
    ("medium-hp-thap", "medium", dict(tank_hp=1, base_hp=1, wall_hp=1), 4, 3),
    ("full-hp-thap", "full", dict(tank_hp=1, base_hp=1, wall_hp=1), 4, 4),
]

CONFIGS = [
    ("Minimax", MinimaxSearch, False),
    ("Alpha-Beta", AlphaBetaSearch, False),
    ("Alpha-Beta + ordering", AlphaBetaSearch, True),
]

FIELDS = ["scenario", "horizon", "algorithm", "value", "action", "nodes_generated",
          "nodes_expanded", "terminal_nodes", "pruned_branches", "cutoffs", "max_depth_ply",
          "time_s"]


def run(max_horizon, minimax_max_horizon):
    rows = []
    for name, map_name, hp, warm, seed in SCENARIOS:
        start = warmup(set_hp(load_state(map_name), **hp), warm, seed)
        if start.is_terminal():
            continue
        for horizon in range(1, max_horizon + 1):
            values = {}
            for label, cls, ordering in CONFIGS:
                if cls is MinimaxSearch and horizon > minimax_max_horizon:
                    continue
                res = cls(move_ordering=ordering, horizon=horizon).search(start)
                st = res.stats
                values[label] = res.value
                rows.append(dict(
                    scenario=name, horizon=horizon, algorithm=label, value=res.value,
                    action=res.action.name, nodes_generated=st.nodes_generated,
                    nodes_expanded=st.nodes_expanded, terminal_nodes=st.terminal_nodes,
                    pruned_branches=st.pruned_branches, cutoffs=st.cutoffs,
                    max_depth_ply=st.max_depth, time_s=round(st.elapsed, 4)))
            if len(set(values.values())) != 1:
                raise AssertionError("Giá trị gốc khác nhau: %s h=%d %s" % (name, horizon, values))
    return rows


def print_table(rows):
    cols = ["scenario", "horizon", "algorithm", "value", "action", "nodes_generated",
            "pruned_branches", "max_depth_ply", "time_s"]
    widths = [max(len(c), max(len(str(r[c])) for r in rows)) for c in cols]
    print("  ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(r[c]).ljust(w) for c, w in zip(cols, widths)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-horizon", type=int, default=3, help="số cycle nhìn trước tối đa")
    ap.add_argument("--minimax-max-horizon", type=int, default=None,
                    help="horizon lớn nhất chạy Minimax thuần (mặc định bằng --max-horizon)")
    ap.add_argument("--csv", default=None, help="ghi kết quả ra file csv")
    args = ap.parse_args()

    mm_h = args.minimax_max_horizon if args.minimax_max_horizon is not None else args.max_horizon
    rows = run(args.max_horizon, mm_h)
    print_table(rows)
    print("\nMọi thuật toán đều cho cùng giá trị gốc trên mỗi kịch bản và horizon.")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print("Đã ghi", args.csv)


if __name__ == "__main__":
    main()
