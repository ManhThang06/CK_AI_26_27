import csv
import random
import statistics
from pathlib import Path
from .min_conflicts import MinConflictsSolver, slow_conflicts

N_VALUES = [8, 16, 32, 64, 100, 200]
SEEDS = list(range(1, 31))
VARIANTS = ["standard", "max_tabu", "roulette"]
MAX_STEPS = 20000

def restart_limit(n):
    return max(50, n)

def run_all(n_values=N_VALUES, seeds=SEEDS, variants=VARIANTS, max_steps=MAX_STEPS, restart=False):
    rows = []
    for n in n_values:
        tabu = max(2, min(10, n // 5))
        for seed in seeds:
            init_rng = random.Random(seed)
            init = [init_rng.randrange(n) for _ in range(n)]
            for v in variants:
                solver = MinConflictsSolver(
                    n, max_steps, v, tabu,
                    restart_after=restart_limit(n) if restart else None,
                )
                res = solver.solve(initial_state=init, seed=seed)
                ok = res["success"] and slow_conflicts(res["solution"]) == 0   # Kiểm tra độc lập.
                rows.append({"N": n, "variant": v, "seed": seed, "steps": res["steps"],
                             "time": "%.6f" % res["time_sec"], "success": int(ok)})
    return rows

def save_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["N", "variant", "seed", "steps", "time", "success"])
        w.writeheader()
        w.writerows(rows)

def summarize(rows):
    out = []
    for n in sorted({int(r["N"]) for r in rows}):
        for v in dict.fromkeys(r["variant"] for r in rows if int(r["N"]) == n):
            g = [r for r in rows if int(r["N"]) == n and r["variant"] == v]
            ok = [r for r in g if int(r["success"])]
            st = [int(r["steps"]) for r in g]
            tm = [float(r["time"]) * 1000 for r in g]
            out.append((n, v, 100.0 * len(ok) / len(g), statistics.median(st), statistics.mean(st),
                        statistics.pstdev(st), statistics.mean(tm), len(g) - len(ok)))
    return out

def print_summary(summary):
    print("Số bước và thời gian tính trên mọi lần chạy, gồm cả lần hết ngân sách.")
    print("%4s %-9s %8s %8s %8s %8s %9s %5s" % ("N", "variant", "succ(%)", "med_st", "mean_st", "std_st", "ms/run", "fail"))
    for n, v, sr, med, mean, sd, ms, fail in summary:
        print("%4d %-9s %8.1f %8.1f %8.1f %8.1f %9.2f %5d" % (n, v, sr, med, mean, sd, ms, fail))

if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parents[1] / "experiments"
    rows = run_all()                      
    save_csv(rows, output_dir / "t1_minconflicts_runs.csv")
    print_summary(summarize(rows))
    rows_rr = run_all(restart=True)      
    save_csv(rows_rr, output_dir / "t1_minconflicts_runs_restart.csv")
    print_summary(summarize(rows_rr))