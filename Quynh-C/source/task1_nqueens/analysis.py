import csv
import math
import os
import statistics
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("%s has no data rows" % path)
    for row in rows:
        for key, val in row.items():
            try:
                row[key] = float(val) if "." in val else int(val)
            except ValueError:
                pass
    return rows

def group_mean(rows, group_key, x_key, y_key):
    buckets = defaultdict(list)
    for row in rows:
        group = row[group_key] if group_key else "all"
        buckets[(group, row[x_key])].append(row[y_key])
    result = defaultdict(list)
    for (group, x), ys in buckets.items():
        result[group].append((x, sum(ys) / len(ys)))
    return {g: sorted(pts) for g, pts in result.items()}

def require_columns(rows, columns, path):
    missing = [c for c in columns if c not in rows[0]]
    if missing:
        raise ValueError("%s is missing columns: %s" % (path, ", ".join(missing)))

def plot_lines(series, xlabel, ylabel, title, out_path, logy=False):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.figure(figsize=(5, 3.2))
    for label, pts in series.items():
        xs, ys = zip(*pts)
        plt.plot(xs, ys, marker="o", label=label)
    if logy:
        plt.yscale("log")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    if len(series) > 1:
        plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def plot_sat(csv_path, out_dir):
    rows = load_csv(csv_path)
    require_columns(rows, ["N", "num_clauses", "gen_time", "solve_time"], csv_path)
    clauses = {"clauses": group_mean(rows, None, "N", "num_clauses")["all"]}
    plot_lines(clauses, "N", "number of CNF clauses", "Clauses vs N",
               out_dir + "/sat_clauses.png", logy=True)
    times = {
        "encode": group_mean(rows, None, "N", "gen_time")["all"],
        "solve": group_mean(rows, None, "N", "solve_time")["all"],
    }
    plot_lines(times, "N", "time (s)", "Running time vs N",
               out_dir + "/sat_time.png", logy=True)

def plot_minconf(csv_path, out_dir):
    rows = load_csv(csv_path)
    require_columns(rows, ["N", "variant", "steps", "time"], csv_path)
    plot_lines(group_mean(rows, "variant", "N", "steps"), "N", "mean steps",
               "Min-Conflicts: steps", out_dir + "/minconf_steps.png")
    plot_lines(group_mean(rows, "variant", "N", "time"), "N", "mean time (s)",
               "Min-Conflicts: time", out_dir + "/minconf_time.png")

def clauses_formula(n):
    # row ALO (n) + at-most-one on every row, column and both diagonal families
    pairs = lambda m: m * (m - 1) // 2
    diag = sum(pairs(n - abs(k)) for k in range(-(n - 1), n))
    return n + 2 * n * pairs(n) + 2 * diag


def sat_table(rows):
    # one summary row per N: median time and min/max over the repeated trials
    by_n = defaultdict(list)
    for row in rows:
        by_n[row["N"]].append(row)
    table = []
    for n in sorted(by_n):
        trials = by_n[n]
        entry = {"N": n, "num_vars": trials[0]["num_vars"],
                 "num_clauses": trials[0]["num_clauses"], "trials": len(trials)}
        for key in ("gen_time", "load_time", "solve_time"):
            if key in trials[0]:
                vals = [t[key] for t in trials]
                entry[key] = (statistics.median(vals), min(vals), max(vals))
        table.append(entry)
    return table


def plot_sat_report(csv_path, out_dir):
    # task 1.2 figures for the report (single IEEE column wide)
    rows = load_csv(csv_path)
    require_columns(rows, ["N", "num_vars", "num_clauses", "gen_time", "solve_time"], csv_path)
    table = sat_table(rows)
    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams.update({"font.family": "serif", "font.size": 8})

    ns = [t["N"] for t in table]
    clauses = [t["num_clauses"] for t in table]
    slope = statistics.linear_regression([math.log(n) for n in ns],
                                         [math.log(c) for c in clauses]).slope
    plt.figure(figsize=(3.4, 2.5))
    plt.loglog(ns, clauses, "ko-", ms=3, label="clauses")
    plt.xlabel("N (board size)")
    plt.ylabel("number of CNF clauses")
    plt.title("Clauses vs N (log-log slope %.2f)" % slope)
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir + "/sat_clauses.png", dpi=300)
    plt.close()

    plt.figure(figsize=(3.4, 2.5))
    styles = [("gen_time", "encode", "ks-"), ("load_time", "load", "g^-"), ("solve_time", "solve", "ro-")]
    for key, label, fmt in styles:
        if key not in table[0]:
            continue
        mid = [t[key][0] for t in table]
        low = [t[key][0] - t[key][1] for t in table]
        high = [t[key][2] - t[key][0] for t in table]
        plt.errorbar(ns, mid, yerr=[low, high], fmt=fmt, ms=3, lw=1, capsize=2, label=label)
    plt.yscale("log")
    plt.xlabel("N (board size)")
    plt.ylabel("time (s), median with min-max")
    plt.title("Running time vs N")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir + "/sat_time.png", dpi=300)
    plt.close()

    with open(out_dir + "/sat_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["N", "num_vars", "num_clauses", "encode_s", "load_s", "solve_s", "trials"])
        for t in table:
            w.writerow([t["N"], t["num_vars"], t["num_clauses"], "%.6f" % t["gen_time"][0],
                        "%.6f" % t.get("load_time", (0,))[0], "%.6f" % t["solve_time"][0], t["trials"]])
    return table, slope


if __name__ == "__main__":
    # python task1_nqueens/analysis.py                      -> sample data
    # python task1_nqueens/analysis.py sat.csv              -> report figures for 1.2
    # python task1_nqueens/analysis.py sat.csv minconf.csv  -> also 1.3
    report_dir = "../report/figures"
    if len(sys.argv) == 1:
        plot_sat("task1_nqueens/data/sample_sat.csv", "task1_nqueens/figures")
        plot_minconf("task1_nqueens/data/sample_minconf.csv", "task1_nqueens/figures")
        print("sample figures saved in task1_nqueens/figures")
    else:
        plot_sat_report(sys.argv[1], report_dir)
        if len(sys.argv) > 2:
            plot_minconf(sys.argv[2], report_dir)
        print("figures saved in", os.path.abspath(report_dir))
