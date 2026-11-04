from itertools import combinations

class Propagation:

    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.cache = {}

    def combinations_for(self, count, total):
        key = (count, total)
        if key not in self.cache:
            self.cache[key] = [set(c) for c in combinations(range(1, 10), count) if sum(c) == total]
        return self.cache[key]

    def filter(self, assignment, domains, emit, depth):
        removed = []
        for run in self.puzzle.runs:
            used = [assignment[c] for c in run.cells if c in assignment]
            unassigned = [c for c in run.cells if c not in assignment]
            if len(used) != len(set(used)):
                return False, removed
            remaining = run.target - sum(used)
            if not unassigned:
                if remaining != 0:
                    return False, removed
                continue
            union = set().union(*(domains[c] for c in unassigned))
            allowed = set()
            for combo in self.combinations_for(len(unassigned), remaining):
                if not combo.intersection(used) and combo <= union:
                    allowed.update(combo)
            for cell in unassigned:
                deleted = sorted(domains[cell] - allowed)
                for value in deleted:
                    domains[cell].remove(value)
                    removed.append((cell, value))
                if deleted:
                    emit("propagate", cell, deleted, run.id, depth)
                if not domains[cell]:
                    return False, removed
        return True, removed

    @staticmethod
    def restore(domains, removed):
        for cell, value in reversed(removed):
            domains[cell].add(value)