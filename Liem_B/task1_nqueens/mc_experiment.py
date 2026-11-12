"""Thuc nghiem 1.3: Min-Conflicts chuan vs cac heuristic chon bien.

Xuat CSV moi dong = 1 lan chay, dung cot cua analysis.py (C): N,variant,seed,steps,time,success
 - cung (N, seed) -> cung trang thai khoi tao, cung max_steps cho moi variant
 - restart=True: them random restart (xep lai ban co neu restart_limit(N) buoc khong cai thien)
 - steps/time ghi ca khi that bai (steps = max_steps), de khong bi lech khi tinh trung binh
"""
import csv
import random
import statistics

from CK_AI_26_27.Liem_B.task1_nqueens.min_conflicts import MinConflictsSolver, slow_conflicts

N_VALUES = [8, 16, 32, 64, 100, 200]
SEEDS = list(range(1, 31))
VARIANTS = ["standard", "max_tabu", "roulette"]
MAX_STEPS = 20000


def restart_limit(n):
    """Ngung cai thien bao nhieu buoc thi xep lai ban co (chi dung khi restart=True)."""
    return max(50, n)


def run_all(n_values=N_VALUES, seeds=SEEDS, variants=VARIANTS, max_steps=MAX_STEPS, restart=False):
    rows = []
    for n in n_values:
        tabu = max(2, min(10, n // 5))
        for seed in seeds:
            init_rng = random.Random(seed)
            init = [init_rng.randrange(n) for _ in range(n)]
            for v in variants:
                res = MinConflictsSolver(n, max_steps, v, tabu, restart_after=restart_limit(n) if restart else None).solve(initial_state=init, seed=seed)
                ok = res["success"] and slow_conflicts(res["solution"]) == 0   # kiem tra doc lap
                rows.append({"N": n, "variant": v, "seed": seed, "steps": res["steps"],
                             "time": "%.6f" % res["time_sec"], "success": int(ok)})
    return rows


def save_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["N", "variant", "seed", "steps", "time", "success"])
        w.writeheader()
        w.writerows(rows)


def summarize(rows):
    """Bang tom tat: ti le thanh cong, trung vi/TB so buoc (chi lan thanh cong), thoi gian."""
    out = []
    for n in sorted({r["N"] for r in rows}):
        for v in VARIANTS:
            g = [r for r in rows if r["N"] == n and r["variant"] == v]
            ok = [r for r in g if r["success"]]
            st = [r["steps"] for r in ok] or [float("nan")]
            tm = [float(r["time"]) * 1000 for r in ok] or [float("nan")]
            out.append((n, v, 100.0 * len(ok) / len(g), statistics.median(st), statistics.mean(st),
                        statistics.pstdev(st), statistics.mean(tm), len(g) - len(ok)))
    return out


def print_summary(summary):
    print("%4s %-9s %8s %8s %8s %8s %9s %5s" % ("N", "variant", "succ(%)", "med_st", "mean_st", "std_st", "ms/run", "fail"))
    for n, v, sr, med, mean, sd, ms, fail in summary:
        print("%4d %-9s %8.1f %8.1f %8.1f %8.1f %9.2f %5d" % (n, v, sr, med, mean, sd, ms, fail))


if __name__ == "__main__":
    rows = run_all()                      # Min-Conflicts thuan (Lec 08)
    save_csv(rows, "experiments/t1_minconflicts_runs.csv")
    print_summary(summarize(rows))
    rows_rr = run_all(restart=True)       # them random restart khi bi ket
    save_csv(rows_rr, "experiments/t1_minconflicts_runs_restart.csv")
    print_summary(summarize(rows_rr))
