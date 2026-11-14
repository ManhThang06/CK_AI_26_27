"""Dong lenh: python -m task3_kakuro <solve|bench|test> ... (chay tu thu muc cha cua task3_kakuro).

  solve [puzzle ...] | --all   giai puzzle, in nghiem va thong ke
  bench                        so sanh cac to hop heuristic tren MOI puzzle trong puzzles/
  test                         chay bo kiem thu tu dong (unittest)

Giao dien: python -m task3_kakuro.ui.app
"""
import argparse
import statistics
import sys
import unittest
from pathlib import Path

from .puzzle import PUZZLE_DIR, Puzzle, load_all
from .solver import BacktrackingSolver, VARIABLE_SELECTORS, VALUE_ORDERERS


def build_solver(puzzle, variable, value, max_nodes):
    return BacktrackingSolver(puzzle, VARIABLE_SELECTORS[variable](),
                              VALUE_ORDERERS[value](), max_nodes=max_nodes)


def print_grid(puzzle, solution):
    for r, row in enumerate(puzzle.grid):
        print(" ".join(str(solution[f"{r},{c}"]) if t == "." else "#" for c, t in enumerate(row)))


def print_warnings(puzzle, prefix="  "):
    for warning in puzzle.warnings:
        print(f"{prefix}[canh bao] {warning}")


def report_load_errors(errors):
    for path, message in errors:
        print(f"[bo qua] {Path(path).name}: {message}", file=sys.stderr)


def solve_one(puzzle, variable, value, max_nodes):
    result = build_solver(puzzle, variable, value, max_nodes).solve()
    s = result.stats
    print(f"{puzzle.name}: {result.status}, verified={result.verified}")
    print_warnings(puzzle)
    print(f"  config={variable}+{value}  nodes={s.nodes}  backtracks={s.backtracks}  "
          f"max_depth={s.max_depth}  pruned_init={s.pruned_init}  time={result.seconds * 1000:.2f} ms")
    if result.solution:
        print_grid(puzzle, result.solution)
    return result


def cmd_solve(args):
    if args.all or not args.puzzles:
        puzzles, errors = load_all()
        report_load_errors(errors)
    else:
        puzzles = [Puzzle.load(path) for path in args.puzzles]
    if not puzzles:
        print(f"Khong co puzzle nao trong {PUZZLE_DIR}", file=sys.stderr)
        return 2
    statuses = [solve_one(p, args.variable, args.value, args.max_nodes).status for p in puzzles]
    # Ma thoat: 0 neu moi puzzle deu giai duoc; puzzle vo nghiem la ket qua hop le nhung bao 1
    return 0 if all(s == "solved" for s in statuses) else 1


def cmd_bench(args):
    puzzles, errors = load_all()
    report_load_errors(errors)
    print(f"{'puzzle':<9}{'vars':>5}{'variable':>12}{'value':>7}{'status':>12}{'ok':>7}"
          f"{'nodes':>8}{'backtr':>8}{'depth':>7}{'ms(median)':>12}")
    for puzzle in puzzles:
        for variable in VARIABLE_SELECTORS:
            for value in VALUE_ORDERERS:
                times = []
                for _ in range(args.repeat):
                    result = build_solver(puzzle, variable, value, args.max_nodes).solve()
                    times.append(result.seconds * 1000)
                s = result.stats
                print(f"{puzzle.label:<9}{len(puzzle.cells):>5}{variable:>12}{value:>7}"
                      f"{result.status:>12}{str(result.verified):>7}{s.nodes:>8}{s.backtracks:>8}"
                      f"{s.max_depth:>7}{statistics.median(times):>12.2f}")
        for warning in puzzle.warnings:
            print(f"  ^ {puzzle.label}: [canh bao] {warning}")
    return 0


def cmd_test(args):
    start = Path(__file__).resolve().parent / "tests"
    suite = unittest.defaultTestLoader.discover(str(start), top_level_dir=str(start.parents[1]))
    result = unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(prog="task3_kakuro", description="Kakuro CSP solver")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("solve", help="giai puzzle (mac dinh: moi puzzle trong puzzles/)")
    p.add_argument("puzzles", nargs="*", type=Path)
    p.add_argument("--all", action="store_true", help="giai moi puzzle trong thu muc puzzles/")
    p.add_argument("--variable", choices=VARIABLE_SELECTORS, default="mrv-degree")
    p.add_argument("--value", choices=VALUE_ORDERERS, default="lcv")
    p.add_argument("--max-nodes", type=int, default=None)
    p.set_defaults(func=cmd_solve)

    p = sub.add_parser("bench", help="so sanh cac to hop heuristic tren moi puzzle")
    p.add_argument("--repeat", type=int, default=20)
    p.add_argument("--max-nodes", type=int, default=200000)
    p.set_defaults(func=cmd_bench)

    p = sub.add_parser("test", help="chay bo kiem thu tu dong")
    p.add_argument("-v", "--verbosity", type=int, default=1)
    p.set_defaults(func=cmd_test)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
