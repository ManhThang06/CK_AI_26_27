import argparse
import csv
import json
import platform
import random
import statistics
from pathlib import Path
from .min_conflicts import MinConflictsSolver, slow_conflicts
from .analysis import plot_minconf, plot_tabu

N_VALUES = [8, 16, 32, 64, 100, 200]
SEEDS = list(range(1, 31))
VARIANTS = ["standard", "max_tabu", "roulette"]
MAX_STEPS = 20000
TABU_SIZES = [0, 2, 5, 10, 20]
RUN_FIELDS = ["N", "variant", "seed", "steps", "time", "success", "restarts"]
TABU_FIELDS = ["N", "tabu_size", "seed", "steps", "time", "success", "restarts"]


def restart_limit(n):
    return max(50, n)


def default_tabu(n):
    return max(2, min(10, n // 5))


def run_all(n_values=N_VALUES, seeds=SEEDS, variants=VARIANTS, max_steps=MAX_STEPS, restart=False):
    rows = []
    for n in n_values:
        tabu = default_tabu(n)
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
                             "time": "%.6f" % res["time_sec"], "success": int(ok),
                             "restarts": res["restarts"]})
    return rows


def run_tabu_study(n_values=N_VALUES, seeds=SEEDS, tabu_sizes=TABU_SIZES, max_steps=MAX_STEPS):
    """Thay đổi tabu_size của max_tabu (có restart) để biện luận cho công thức default_tabu."""
    rows = []
    for n in n_values:
        for seed in seeds:
            init_rng = random.Random(seed)
            init = [init_rng.randrange(n) for _ in range(n)]
            for tabu in tabu_sizes:
                solver = MinConflictsSolver(n, max_steps, "max_tabu", tabu,
                                            restart_after=restart_limit(n))
                res = solver.solve(initial_state=init, seed=seed)
                ok = res["success"] and slow_conflicts(res["solution"]) == 0
                rows.append({"N": n, "tabu_size": tabu, "seed": seed, "steps": res["steps"],
                             "time": "%.6f" % res["time_sec"], "success": int(ok),
                             "restarts": res["restarts"]})
    return rows


def save_csv(rows, path, fieldnames=RUN_FIELDS):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
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


def print_tabu_summary(rows):
    print("Thí nghiệm tabu_size của max_tabu (có restart): median số bước / tỉ lệ thành công")
    sizes = sorted({int(r["tabu_size"]) for r in rows})
    print("%4s " % "N" + " ".join("%14s" % ("tabu=%d" % s) for s in sizes))
    for n in sorted({int(r["N"]) for r in rows}):
        cells = []
        for s in sizes:
            g = [r for r in rows if int(r["N"]) == n and int(r["tabu_size"]) == s]
            med = statistics.median(int(r["steps"]) for r in g)
            sr = 100.0 * sum(int(r["success"]) for r in g) / len(g)
            cells.append("%7.1f /%4.0f%%" % (med, sr))
        print("%4d " % n + " ".join("%14s" % c for c in cells))


def main(output_dir, seeds, n_values):
    output_dir = Path(output_dir)
    rows = run_all(n_values, seeds)
    save_csv(rows, output_dir / "minconf.csv")
    print("== Không restart ==")
    print_summary(summarize(rows))
    rows_rr = run_all(n_values, seeds, restart=True)
    save_csv(rows_rr, output_dir / "minconf_restart.csv")
    print("== Có restart ==")
    print_summary(summarize(rows_rr))
    tabu_rows = run_tabu_study(n_values, seeds)
    save_csv(tabu_rows, output_dir / "minconf_tabu.csv", TABU_FIELDS)
    print_tabu_summary(tabu_rows)
    plot_minconf(str(output_dir / "minconf.csv"), str(output_dir / "figures"), suffix="")
    plot_minconf(str(output_dir / "minconf_restart.csv"), str(output_dir / "figures"), suffix="_restart")
    plot_tabu(str(output_dir / "minconf_tabu.csv"), str(output_dir / "figures"))
    (output_dir / "environment_minconf.json").write_text(json.dumps({
        "platform": platform.platform(), "python": platform.python_version(),
        "N": list(n_values), "seeds": len(seeds), "max_steps": MAX_STEPS, "tabu_sizes": TABU_SIZES,
        "restart_after": "max(50, N)", "default_tabu": "max(2, min(10, N // 5))",
        "note": "cùng trạng thái khởi tạo cho mọi biến thể trong một seed; thời gian phụ thuộc máy"},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print("Đã lưu CSV và biểu đồ vào", output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thực nghiệm Min-Conflicts: so sánh 3 cách chọn biến.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "data/measured")
    parser.add_argument("--seeds", type=int, default=len(SEEDS), help="số seed mỗi cấu hình (mặc định 30)")
    parser.add_argument("--ns", nargs="+", type=int, default=N_VALUES)
    args = parser.parse_args()
    main(args.output, list(range(1, args.seeds + 1)), args.ns)
