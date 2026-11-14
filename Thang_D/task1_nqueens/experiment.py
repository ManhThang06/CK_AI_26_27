import argparse
import csv
import json
import platform
import statistics
from importlib.metadata import version
from pathlib import Path
from .sat_solver import SATSolver
from .analysis import plot_sat

def run(ns, repeats, output):
    if repeats < 1 or not ns or any(n < 4 or n > 64 for n in ns):
        raise ValueError("Use 4 <= N <= 64 and repeats >= 1")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for n in ns:
        for trial in range(1, repeats + 1):
            result = SATSolver().solve(n)
            result.pop("columns")
            rows.append({**result, "trial": trial})
    with (output / "sat.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for n in ns:
        trials = [r for r in rows if r["N"] == n]
        times = [r["solve_time"] for r in trials]
        summary.append({"N": n, "num_clauses": trials[0]["num_clauses"],
                        "mean_s": statistics.mean(times),
                        "stdev_s": statistics.stdev(times) if repeats > 1 else 0})
    with (output / "sat_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    (output / "environment.json").write_text(json.dumps({"platform": platform.platform(),
        "python": platform.python_version(), "python-sat": version("python-sat"),
        "repeats": repeats, "N": ns, "note": "new solver per trial, sequential; no timeout"}, indent=2))
    plot_sat(str(output / "sat.csv"), str(output / "figures"))
    for row in summary:
        print(row)
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ns", nargs="+", type=int, default=[4, 5, 8, 12, 16, 24, 32, 48, 64])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data/measured")
    args = parser.parse_args()
    run(args.ns, args.repeats, args.output)