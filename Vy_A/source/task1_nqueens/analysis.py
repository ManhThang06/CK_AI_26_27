import csv
import os
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

if __name__ == "__main__":
    sat = sys.argv[1] if len(sys.argv) > 1 else "task1_nqueens/data/sample_sat.csv"
    mc = sys.argv[2] if len(sys.argv) > 2 else "task1_nqueens/data/sample_minconf.csv"
    plot_sat(sat, "task1_nqueens/figures")
    plot_minconf(mc, "task1_nqueens/figures")
    print("figures saved in task1_nqueens/figures")