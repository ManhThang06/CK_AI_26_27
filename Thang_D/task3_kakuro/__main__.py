"""Dong lenh: python -m task3_kakuro <solve|traces|bench> ... (chay tu thu muc cha cua task3_kakuro)."""
import argparse
import statistics
from pathlib import Path

from .puzzle import Puzzle
from .solver import (BacktrackingSolver, TraceRecorder,
                     VARIABLE_SELECTORS, VALUE_ORDERERS)

ROOT = Path(__file__).resolve().parent
PUZZLES = ROOT / "puzzles"
TRACES = ROOT / "traces"

# (ten file trace, file puzzle, bien, gia tri)
DEFAULT_TRACES = [
    ("assignment_5x5.json", "assignment_5x5.json", "mrv-degree", "lcv"),
    ("assignment_9x9.json", "assignment_9x9.json", "mrv-degree", "lcv"),
    ("backtrack_demo.json", "assignment_9x9.json", "mrv", "asc"),   # thu nhieu lan quay lui
]


def build_solver(puzzle, variable, value, max_nodes, record=False):
    solver = BacktrackingSolver(puzzle, VARIABLE_SELECTORS[variable](),
                                      VALUE_ORDERERS[value](), max_nodes=max_nodes)
    if record:
        solver.rec = TraceRecorder(puzzle, solver.stats, solver.config)
    return solver


def print_grid(puzzle, solution):
    for r, row in enumerate(puzzle.grid):
        print(" ".join(str(solution[f"{r},{c}"]) if t == "." else "#" for c, t in enumerate(row)))


def cmd_solve(args):
    puzzle = Puzzle.load(args.puzzle)
    solver = build_solver(puzzle, args.variable, args.value, args.max_nodes, record=bool(args.trace))
    result = solver.solve()
    s = result.stats
    print(f"{puzzle.name}: {result.status}, verified={result.verified}")
    print(f"  config={args.variable}+{args.value}  nodes={s.nodes}  backtracks={s.backtracks}  "
          f"max_depth={s.max_depth}  pruned_init={s.pruned_init}  time={result.seconds * 1000:.2f} ms")
    if result.solution:
        print_grid(puzzle, result.solution)
    if args.trace:
        solver.rec.save(args.trace)
        print(f"  trace: {len(solver.rec.events)} events -> {args.trace}")
    return 0 if result.status == "solved" else 1


def cmd_traces(args):
    for trace_name, puzzle_name, variable, value in DEFAULT_TRACES:
        puzzle = Puzzle.load(PUZZLES / puzzle_name)
        solver = build_solver(puzzle, variable, value, args.max_nodes, record=True)
        result = solver.solve()
        solver.rec.save(TRACES / trace_name)
        print(f"{trace_name}: {variable}+{value}, {result.status}, "
              f"{len(solver.rec.events)} events, nodes={result.stats.nodes}, "
              f"backtracks={result.stats.backtracks}")
    return 0


def cmd_bench(args):
    print(f"{'puzzle':<16}{'variable':<12}{'value':<7}{'status':<8}{'ok':<6}{'nodes':>7}"
          f"{'backtr':>8}{'depth':>7}{'ms(median)':>12}")
    for path in sorted(PUZZLES.glob("*.json")):
        puzzle = Puzzle.load(path)
        for variable in VARIABLE_SELECTORS:
            for value in VALUE_ORDERERS:
                times = []
                for _ in range(args.repeat):
                    result = build_solver(puzzle, variable, value, args.max_nodes).solve()
                    times.append(result.seconds * 1000)
                s = result.stats
                print(f"{path.stem:<16}{variable:<12}{value:<7}{result.status:<8}"
                      f"{str(result.verified):<6}{s.nodes:>7}{s.backtracks:>8}{s.max_depth:>7}"
                      f"{statistics.median(times):>12.2f}")
    return 0


def main():
    parser = argparse.ArgumentParser(prog="task3_kakuro", description="Kakuro CSP solver")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("solve", help="giai mot puzzle, tuy chon xuat trace cho UI")
    p.add_argument("puzzle", type=Path)
    p.add_argument("--variable", choices=VARIABLE_SELECTORS, default="mrv-degree")
    p.add_argument("--value", choices=VALUE_ORDERERS, default="lcv")
    p.add_argument("--max-nodes", type=int, default=None)
    p.add_argument("--trace", type=Path, help="ghi trace JSON de phat lai trong UI")
    p.set_defaults(func=cmd_solve)

    p = sub.add_parser("traces", help="sinh lai cac trace mac dinh trong traces/")
    p.add_argument("--max-nodes", type=int, default=None)
    p.set_defaults(func=cmd_traces)

    p = sub.add_parser("bench", help="so sanh cac to hop heuristic tren moi puzzle")
    p.add_argument("--repeat", type=int, default=20)
    p.add_argument("--max-nodes", type=int, default=200000)
    p.set_defaults(func=cmd_bench)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
