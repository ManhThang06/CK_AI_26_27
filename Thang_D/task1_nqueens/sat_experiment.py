import argparse
import platform
import statistics
from importlib.metadata import version
from pathlib import Path
from .experiment_base import Experiment
from .sat_solver import SATSolver
from .analysis import SATPlotter


class SATExperiment(Experiment):
    """Đo số clause và thời gian giải của Glucose3 khi N tăng dần."""

    DEFAULT_NS = [4, 5, 8, 12, 16, 24, 32, 48, 64]

    def __init__(self, ns=None, repeats=5, output=None):
        super().__init__(output or Path(__file__).parent / "data/measured")
        self.ns = list(ns) if ns else list(self.DEFAULT_NS)
        self.repeats = repeats
        if repeats < 1 or any(n < 4 or n > 64 for n in self.ns):
            raise ValueError("Use 4 <= N <= 64 and repeats >= 1")

    def measure(self):
        rows = []
        for n in self.ns:
            for trial in range(1, self.repeats + 1):
                result = SATSolver().solve(n)
                result.pop("solution")
                rows.append({**result, "trial": trial})
        return rows

    def summarize(self, rows):
        summary = []
        for n in self.ns:
            trials = [r for r in rows if r["N"] == n]
            times = [r["solve_time"] for r in trials]
            summary.append({"N": n, "num_clauses": trials[0]["num_clauses"],
                            "mean_s": statistics.mean(times),
                            "stdev_s": statistics.stdev(times) if self.repeats > 1 else 0})
        return summary

    def run(self):
        rows = self.measure()
        self.save_csv(rows, "sat.csv")
        summary = self.summarize(rows)
        self.save_csv(summary, "sat_summary.csv")
        self.save_environment("environment.json", {
            "platform": platform.platform(), "python": platform.python_version(),
            "python-sat": version("python-sat"), "repeats": self.repeats, "N": self.ns,
            "note": "new solver per trial, sequential; no timeout"})
        SATPlotter(str(self.output / "sat.csv"), str(self.output / "figures")).plot()
        for row in summary:
            print(row)
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ns", nargs="+", type=int, default=SATExperiment.DEFAULT_NS)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data/measured")
    args = parser.parse_args()
    SATExperiment(args.ns, args.repeats, args.output).run()
