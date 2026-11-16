"""Giải đấu vòng tròn giữa các agent (4 thuật toán có sẵn và các plugin trong plugins/).

Mỗi cặp đấu trên cả ba map và đổi bên (agent A làm P1 rồi làm P2). HP chuẩn 6/9/3.
Thống kê thắng/hòa/thua và thời gian suy nghĩ trung bình mỗi nước.

Chạy (từ thư mục chứa task2_tank):
    python -m task2_tank.experiments.tournament --depth 2
"""

import argparse
import csv
import itertools
import os

from ..algorithms.scenarios import load_state
from ..engine.match import MatchSession
from ..gui.agent_registry import build_registry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--maps", default="small,medium,full")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args()

    specs, errors = build_registry()
    for fn, msg in errors:
        print("plugin lỗi:", fn, msg)
    specs = [s for s in specs if not s.is_human]
    stat = {s.label: dict(w=0, d=0, l=0, time=0.0, moves=0) for s in specs}
    rows = []

    for a, b in itertools.combinations(specs, 2):
        for m in args.maps.split(","):
            for first, second in ((a, b), (b, a)):
                participants = [first.factory(args.depth), second.factory(args.depth)]
                for agent in participants:
                    if hasattr(agent, "time_limit"):
                        agent.time_limit = None
                    search = getattr(agent, "search", None)
                    if search is not None:
                        search.time_limit = None
                match = MatchSession(load_state(m), participants)
                final = match.run()
                ta, tb = match.agents
                u = final.utility()
                win = first.label if u > 0 else second.label if u < 0 else "draw"
                for spec, t in ((first, ta), (second, tb)):
                    stat[spec.label]["time"] += t.total_time
                    stat[spec.label]["moves"] += t.moves
                    if win == "draw":
                        stat[spec.label]["d"] += 1
                    elif win == spec.label:
                        stat[spec.label]["w"] += 1
                    else:
                        stat[spec.label]["l"] += 1
                rows.append(dict(map=m, p1=first.label, p2=second.label, winner=win, cycles=final.cycle))
                print("%-6s P1=%-24s P2=%-24s -> %s (%d cycle)" % (m, first.label, second.label, win,
                                                                  final.cycle), flush=True)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "tournament_games.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["map", "p1", "p2", "winner", "cycles"])
        w.writeheader()
        w.writerows(rows)
    print("\n%-26s %4s %4s %4s %14s" % ("agent", "W", "D", "L", "ms / nước đi"))
    with open(os.path.join(args.out, "tournament_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["agent", "win", "draw", "loss", "ms_per_move"])
        for label, s in stat.items():
            ms = 1000 * s["time"] / max(1, s["moves"])
            print("%-26s %4d %4d %4d %14.2f" % (label, s["w"], s["d"], s["l"], ms))
            w.writerow([label, s["w"], s["d"], s["l"], round(ms, 3)])


if __name__ == "__main__":
    main()
