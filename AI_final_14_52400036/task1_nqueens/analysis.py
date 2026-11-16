import csv
import os
import statistics
from abc import ABC, abstractmethod
from collections import defaultdict
import matplotlib.pyplot as plt


class Plotter(ABC):
    """Lớp cha: đọc CSV, kiểm tra cột, nhóm số liệu và vẽ biểu đồ đường."""

    required_columns = ()

    def __init__(self, csv_path, out_dir):
        self.csv_path = csv_path
        self.out_dir = out_dir
        self.rows = self.load_csv(csv_path)
        self._require_columns()

    @staticmethod
    def _convert(value):
        for cast in (int, float):
            try:
                return cast(value)
            except ValueError:
                pass
        return value

    @classmethod
    def load_csv(cls, path):
        with open(path, newline="", encoding="utf-8") as f:
            rows = [{k: cls._convert(v) for k, v in row.items()} for row in csv.DictReader(f)]
        if not rows:
            raise ValueError("%s has no data rows" % path)
        return rows

    def _require_columns(self):
        missing = [c for c in self.required_columns if c not in self.rows[0]]
        if missing:
            raise ValueError("%s is missing columns: %s" % (self.csv_path, ", ".join(missing)))

    @staticmethod
    def group_stat(rows, group_key, x_key, y_key, func):
        """Gom y theo (nhóm, x) rồi áp `func`; group_key=None nghĩa là một nhóm "all"."""
        buckets = defaultdict(list)
        for row in rows:
            group = row[group_key] if group_key else "all"
            buckets[(group, row[x_key])].append(row[y_key])
        result = defaultdict(list)
        for (group, x), ys in buckets.items():
            result[group].append((x, func(ys)))
        return {g: sorted(pts) for g, pts in result.items()}

    @staticmethod
    def success_rate(values):
        return 100.0 * sum(values) / len(values)

    @staticmethod
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

    @abstractmethod
    def plot(self):
        """Vẽ và lưu các biểu đồ vào `self.out_dir`."""


class SATPlotter(Plotter):
    """Số clause và thời gian (encode, solve) theo N."""

    required_columns = ("N", "num_clauses", "gen_time", "solve_time")

    def plot(self):
        mean = statistics.mean
        clauses = {"clauses": self.group_stat(self.rows, None, "N", "num_clauses", mean)["all"]}
        self.plot_lines(clauses, "N", "number of CNF clauses", "Clauses vs N",
                        self.out_dir + "/sat_clauses.png", logy=True)
        times = {
            "encode": self.group_stat(self.rows, None, "N", "gen_time", mean)["all"],
            "solve": self.group_stat(self.rows, None, "N", "solve_time", mean)["all"],
        }
        self.plot_lines(times, "N", "time (s)", "Running time vs N",
                        self.out_dir + "/sat_time.png", logy=True)


class MinConflictsPlotter(Plotter):
    """Median số bước, median thời gian và tỉ lệ thành công theo N cho từng cách chọn biến."""

    required_columns = ("N", "variant", "steps", "time", "success")

    def __init__(self, csv_path, out_dir, suffix=""):
        super().__init__(csv_path, out_dir)
        self.suffix = suffix

    def plot(self):
        tag = "restart" if self.suffix else "no restart"
        median = statistics.median
        specs = (("steps", "median steps", median, "steps"),
                 ("time", "median time (s)", median, "time"),
                 ("success", "success rate (%)", self.success_rate, "success"))
        for key, ylabel, func, name in specs:
            self.plot_lines(self.group_stat(self.rows, "variant", "N", key, func), "N", ylabel,
                            "Min-Conflicts: %s (%s)" % (name, tag),
                            "%s/minconf_%s%s.png" % (self.out_dir, name, self.suffix))


class TabuPlotter(Plotter):
    """Median số bước của max_tabu theo tabu_size, mỗi đường là một giá trị N."""

    required_columns = ("N", "tabu_size", "steps", "success")

    def plot(self):
        rows = [{**row, "N": "N=%d" % row["N"]} for row in self.rows]
        self.plot_lines(self.group_stat(rows, "N", "tabu_size", "steps", statistics.median),
                        "tabu_size", "median steps", "max_tabu: effect of tabu_size",
                        self.out_dir + "/minconf_tabu.png", legend_outside=True)


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "measured")
    figures = os.path.join(base, "figures")
    SATPlotter(os.path.join(base, "sat.csv"), figures).plot()
    MinConflictsPlotter(os.path.join(base, "minconf.csv"), figures).plot()
    MinConflictsPlotter(os.path.join(base, "minconf_restart.csv"), figures, "_restart").plot()
    TabuPlotter(os.path.join(base, "minconf_tabu.csv"), figures).plot()
    print("figures saved in", figures)
