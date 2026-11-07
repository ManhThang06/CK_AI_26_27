# Writes a sample trace for the 5x5 board. This is only a demo solver
# (row-major order, ascending values) so that the trace has backtracking.
# Run from the source folder: python -m task3_kakuro.tools.make_sample_trace
from task3_kakuro.propagation import Propagator
from task3_kakuro.trace import Trace
from task3_kakuro.tests.test_propagation import RUNS_5X5


def solve(prop, domains, order, assigned, trace):
    if len(assigned) == len(order):
        trace.solved()
        return True
    cell = order[len(assigned)]
    for value in sorted(domains[cell]):
        trace.assign(cell, value)
        ok, removed = prop.assign(domains, cell, value)
        trace.removed(removed)
        if ok:
            assigned.append(cell)
            if solve(prop, domains, order, assigned, trace):
                return True
            assigned.pop()
            trace.backtrack(cell, value, removed)
        else:
            trace.fail(cell, value, prop.failed_run)
            trace.backtrack(cell, value, removed)
        prop.undo(domains, removed)
    return False


if __name__ == "__main__":
    prop = Propagator(RUNS_5X5)
    domains = prop.initial_domains()
    trace = Trace("puzzle_5x5")
    solve(prop, domains, sorted(domains), [], trace)
    trace.save("task3_kakuro/trace_samples/sample_5x5_trace.json")
    print({t: trace.count(t) for t in ("assign", "remove", "fail", "backtrack", "solved")})
