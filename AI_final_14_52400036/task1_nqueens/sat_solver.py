import argparse
from time import perf_counter
from pysat.solvers import Glucose3
from .cnf_encoder import CNFEncoder
from .board import Board
from .nqueens_solver import NQueensSolver


class SATSolver(NQueensSolver):
    """Giải N-quân hậu bằng Glucose3 trên CNF do CNFEncoder sinh ra."""

    def _solve(self, n):
        start = perf_counter()
        encoder = CNFEncoder(n)
        clauses = encoder.encode()
        gen_time = perf_counter() - start
        start = perf_counter()
        with Glucose3(bootstrap_with=clauses) as solver:
            load_time = perf_counter() - start
            start = perf_counter()
            sat = solver.solve()
            solve_time = perf_counter() - start
            model = solver.get_model() if sat else []
        solution = self._decode(encoder, model) if sat else None
        return {"N": n, "num_vars": n * n, "num_clauses": len(clauses),
                "gen_time": gen_time, "load_time": load_time, "solve_time": solve_time,
                "sat": sat, "solution": solution}

    @staticmethod
    def _decode(encoder, model):
        positive = set(value for value in model if value > 0)
        columns = []
        for row in range(encoder.n):
            occupied = [col for col in range(encoder.n) if encoder.variable(row, col) in positive]
            if len(occupied) != 1:
                raise RuntimeError("Invalid SAT model")
            columns.append(occupied[0])
        return columns


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, nargs="?", default=8)
    result = SATSolver().solve(parser.parse_args().n)
    print(result)
    if result["sat"]:
        print(Board(result["solution"]))
