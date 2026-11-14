import csv
import os
import statistics
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

def plot_lines(series, xlabel, ylabel, title, out_path, logy=False, legend_outside=False):
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
        if legend_outside:
            plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
        else:
            plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
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

def group_stat(rows, group_key, x_key, y_key, func):
    buckets = defaultdict(list)
    for row in rows:
        buckets[(row[group_key], row[x_key])].append(row[y_key])
    result = defaultdict(list)
    for (group, x), ys in buckets.items():
        result[group].append((x, func(ys)))
    return {g: sorted(pts) for g, pts in result.items()}

def median(values):
    return statistics.median(values)

def success_rate(values):
    return 100.0 * sum(values) / len(values)

def plot_minconf(csv_path, out_dir, suffix=""):
    """Vẽ median số bước, median thời gian và tỉ lệ thành công theo N cho từng cách chọn biến."""
    rows = load_csv(csv_path)
    require_columns(rows, ["N", "variant", "steps", "time", "success"], csv_path)
    tag = "restart" if suffix else "no restart"
    plot_lines(group_stat(rows, "variant", "N", "steps", median), "N", "median steps",
               "Min-Conflicts: steps (%s)" % tag, out_dir + "/minconf_steps%s.png" % suffix)
    plot_lines(group_stat(rows, "variant", "N", "time", median), "N", "median time (s)",
               "Min-Conflicts: time (%s)" % tag, out_dir + "/minconf_time%s.png" % suffix)
    plot_lines(group_stat(rows, "variant", "N", "success", success_rate), "N", "success rate (%)",
               "Min-Conflicts: success (%s)" % tag, out_dir + "/minconf_success%s.png" % suffix)

def plot_tabu(csv_path, out_dir):
    """Vẽ median số bước của max_tabu theo tabu_size, mỗi đường là một giá trị N."""
    rows = load_csv(csv_path)
    require_columns(rows, ["N", "tabu_size", "steps", "success"], csv_path)
    for row in rows:
        row["N"] = "N=%d" % row["N"]
    plot_lines(group_stat(rows, "N", "tabu_size", "steps", median), "tabu_size", "median steps",
               "max_tabu: effect of tabu_size", out_dir + "/minconf_tabu.png", legend_outside=True)

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "measured")
    plot_sat(os.path.join(base, "sat.csv"), os.path.join(base, "figures"))
    plot_minconf(os.path.join(base, "minconf.csv"), os.path.join(base, "figures"))
    plot_minconf(os.path.join(base, "minconf_restart.csv"), os.path.join(base, "figures"), suffix="_restart")
    plot_tabu(os.path.join(base, "minconf_tabu.csv"), os.path.join(base, "figures"))
    print("figures saved in", os.path.join(base, "figures"))
