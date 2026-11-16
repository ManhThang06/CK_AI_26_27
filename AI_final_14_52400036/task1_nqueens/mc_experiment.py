import argparse
import platform
import random
import statistics
from pathlib import Path
from .experiment_base import Experiment
from .board import Board
from .min_conflicts import MinConflictsSolver
from .analysis import MinConflictsPlotter, TabuPlotter


class MinConflictsExperiment(Experiment):
    """So sánh các cách chọn biến của Min-Conflicts (có/không restart) và ảnh hưởng của tabu_size."""

    N_VALUES = [8, 16, 32, 64, 100, 200]
    SEEDS = list(range(1, 31))
    VARIANTS = ["standard", "max_tabu", "roulette"]
    MAX_STEPS = 20000
    TABU_SIZES = [0, 2, 5, 10, 20]
    RUN_FIELDS = ["N", "variant", "seed", "steps", "time", "success", "restarts"]
    TABU_FIELDS = ["N", "tabu_size", "seed", "steps", "time", "success", "restarts"]

    def __init__(self, output=None, n_values=None, seeds=None, variants=None,
                 max_steps=None, tabu_sizes=None):
        super().__init__(output or Path(__file__).resolve().parent / "data/measured")
        self.n_values = list(n_values or self.N_VALUES)
        self.seeds = list(seeds or self.SEEDS)
        self.variants = list(variants or self.VARIANTS)
        self.max_steps = self.MAX_STEPS if max_steps is None else max_steps
        self.tabu_sizes = list(tabu_sizes or self.TABU_SIZES)

    @staticmethod
    def restart_limit(n):
        return max(50, n)

    @staticmethod
    def default_tabu(n):
        return max(2, min(10, n // 5))

    @staticmethod
    def initial_state(n, seed):
        rng = random.Random(seed)
        return [rng.randrange(n) for _ in range(n)]

    @staticmethod
    def _record(res, **keys):
        ok = res["success"] and Board(res["solution"]).is_valid()  # Kiểm tra độc lập.
        return {**keys, "steps": res["steps"], "time": "%.6f" % res["time_sec"],
                "success": int(ok), "restarts": res["restarts"]}

    def run_variants(self, restart=False):
        rows = []
        for n in self.n_values:
            tabu = self.default_tabu(n)
            for seed in self.seeds:
                init = self.initial_state(n, seed)  # Cùng trạng thái đầu cho mọi biến thể.
                for v in self.variants:
                    solver = MinConflictsSolver(
                        n, self.max_steps, v, tabu,
                        restart_after=self.restart_limit(n) if restart else None)
                    res = solver.solve(initial_state=init, seed=seed)
                    rows.append(self._record(res, N=n, variant=v, seed=seed))
        return rows

    def run_tabu_study(self):
        """Thay đổi tabu_size của max_tabu (có restart) để biện luận cho default_tabu."""
        rows = []
        for n in self.n_values:
            for seed in self.seeds:
                init = self.initial_state(n, seed)
                for tabu in self.tabu_sizes:
                    solver = MinConflictsSolver(n, self.max_steps, "max_tabu", tabu,
                                                restart_after=self.restart_limit(n))
                    res = solver.solve(initial_state=init, seed=seed)
                    rows.append(self._record(res, N=n, tabu_size=tabu, seed=seed))
        return rows

    @staticmethod
    def summarize(rows):
        out = []
        for n in sorted({int(r["N"]) for r in rows}):
            for v in dict.fromkeys(r["variant"] for r in rows if int(r["N"]) == n):
                g = [r for r in rows if int(r["N"]) == n and r["variant"] == v]
                ok = [r for r in g if int(r["success"])]
                st = [int(r["steps"]) for r in g]
                tm = [float(r["time"]) * 1000 for r in g]
                out.append((n, v, 100.0 * len(ok) / len(g), statistics.median(st),
                            statistics.mean(st), statistics.pstdev(st),
                            statistics.mean(tm), len(g) - len(ok)))
        return out

    @staticmethod
    def print_summary(summary):
        print("Số bước và thời gian tính trên mọi lần chạy, gồm cả lần hết ngân sách.")
        print("%4s %-9s %8s %8s %8s %8s %9s %5s" % ("N", "variant", "succ(%)", "med_st", "mean_st", "std_st", "ms/run", "fail"))
        for n, v, sr, med, mean, sd, ms, fail in summary:
            print("%4d %-9s %8.1f %8.1f %8.1f %8.1f %9.2f %5d" % (n, v, sr, med, mean, sd, ms, fail))

    @staticmethod
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

    def run(self):
        rows = self.run_variants()
        self.save_csv(rows, "minconf.csv", self.RUN_FIELDS)
        print("== Không restart ==")
        self.print_summary(self.summarize(rows))
        rows_rr = self.run_variants(restart=True)
        self.save_csv(rows_rr, "minconf_restart.csv", self.RUN_FIELDS)
        print("== Có restart ==")
        self.print_summary(self.summarize(rows_rr))
        tabu_rows = self.run_tabu_study()
        self.save_csv(tabu_rows, "minconf_tabu.csv", self.TABU_FIELDS)
        self.print_tabu_summary(tabu_rows)

        figures = str(self.output / "figures")
        MinConflictsPlotter(str(self.output / "minconf.csv"), figures).plot()
        MinConflictsPlotter(str(self.output / "minconf_restart.csv"), figures, "_restart").plot()
        TabuPlotter(str(self.output / "minconf_tabu.csv"), figures).plot()
        self.save_environment("environment_minconf.json", {
            "platform": platform.platform(), "python": platform.python_version(),
            "N": self.n_values, "seeds": len(self.seeds), "max_steps": self.max_steps,
            "tabu_sizes": self.tabu_sizes,
            "restart_after": "max(50, N)", "default_tabu": "max(2, min(10, N // 5))",
            "note": "cùng trạng thái khởi tạo cho mọi biến thể trong một seed; thời gian phụ thuộc máy"})
        print("Đã lưu CSV và biểu đồ vào", self.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thực nghiệm Min-Conflicts: so sánh 3 cách chọn biến.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "data/measured")
    parser.add_argument("--seeds", type=int, default=len(MinConflictsExperiment.SEEDS),
                        help="số seed mỗi cấu hình (mặc định 30)")
    parser.add_argument("--ns", nargs="+", type=int, default=MinConflictsExperiment.N_VALUES)
    args = parser.parse_args()
    MinConflictsExperiment(args.output, args.ns, list(range(1, args.seeds + 1))).run()
