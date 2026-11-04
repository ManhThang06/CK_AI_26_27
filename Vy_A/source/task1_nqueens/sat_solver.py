import argparse
from time import perf_counter
from pysat.solvers import Glucose3
from .cnf_encoder import CNFEncoder
from .board import Board

class SATSolver:
    def solve(self, n):
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
        positive = set(value for value in model if value > 0)
        columns = None
        if sat:
            columns = []
            for row in range(n):
                occupied = [col for col in range(n) if encoder.variable(row, col) in positive]
                if len(occupied) != 1:
                    raise RuntimeError("Invalid SAT model")
                columns.append(occupied[0])
            if not Board(columns).is_valid():
                raise RuntimeError("Solution failed independent validation")
        return {"N": n, "num_vars": n*n, "num_clauses": len(clauses),
                "gen_time": gen_time, "load_time": load_time, "solve_time": solve_time,
                "sat": sat, "columns": columns}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, nargs="?", default=8)
    result = SATSolver().solve(parser.parse_args().n)
    print(result)
    if result["sat"]:
        print(Board(result["columns"]))