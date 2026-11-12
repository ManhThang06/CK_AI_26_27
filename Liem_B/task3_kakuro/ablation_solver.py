"""Solver Kakuro dung cho thuc nghiem 3.2 (4 cau hinh: BT, +FC, +Sum propagation, +MRV/Degree/LCV)."""
import time


class KakuroCSPSolver:
    def __init__(self, white_cells, clues, use_fc=False, use_prop=False, use_heuristics=False):
        self.white_cells = list(white_cells)
        self.clues = list(clues)
        self.use_fc = use_fc
        self.use_prop = use_prop
        self.use_heuristics = use_heuristics

        # Anh xa moi o trang toi cac run chua no
        self.cell_to_clues = {c: [] for c in self.white_cells}
        self.peers = {c: set() for c in self.white_cells}
        for clue_sum, run_cells in self.clues:
            for c in run_cells:
                self.cell_to_clues[c].append((clue_sum, run_cells))
                for other in run_cells:
                    if other != c:
                        self.peers[c].add(other)

        self.explored_nodes = 0
        self.backtracks = 0

    def _initial_domains(self):
        domains = {c: set(range(1, 10)) for c in self.white_cells}
        if self.use_prop:
            self._propagate_sum_domains(domains, {})
        return domains

    def _propagate_sum_domains(self, domains, assignment):
        """Loc mien gia tri theo tong Run (Constraint Propagation)"""
        changed = True
        while changed:
            changed = False
            for clue_sum, run_cells in self.clues:
                unassigned = [c for c in run_cells if c not in assignment]
                assigned_vals = [assignment[c] for c in run_cells if c in assignment]

                if len(assigned_vals) != len(set(assigned_vals)):
                    return False

                rem_sum = clue_sum - sum(assigned_vals)
                k = len(unassigned)
                if k == 0:
                    if rem_sum != 0:
                        return False
                    continue

                # Gioi han min/max co ban cho moi bien chua gan trong run
                min_other = sum(range(1, k))
                max_other = sum(range(10 - (k - 1), 10))

                for c in unassigned:
                    valid_vals = set()
                    for v in domains[c]:
                        if v not in assigned_vals and (rem_sum - max_other <= v <= rem_sum - min_other):
                            valid_vals.add(v)
                    if not valid_vals:
                        return False
                    if len(valid_vals) < len(domains[c]):
                        domains[c] = valid_vals
                        changed = True
        return True

    def _select_unassigned_var(self, assignment, domains):
        unassigned = [c for c in self.white_cells if c not in assignment]
        if not self.use_heuristics:
            return unassigned[0]

        # MRV + Degree Heuristic
        def mrv_degree_key(cell):
            mrv = len(domains[cell])
            deg = sum(1 for p in self.peers[cell] if p not in assignment)
            return (mrv, -deg)

        return min(unassigned, key=mrv_degree_key)

    def _order_domain_values(self, var, assignment, domains):
        vals = sorted(domains[var])
        if not self.use_heuristics:
            return vals

        # LCV: uu tien gia tri it lam thu hep mien cua cac bien lan can nhat
        def lcv_score(val):
            eliminated = 0
            for p in self.peers[var]:
                if p not in assignment and val in domains[p]:
                    eliminated += 1
            return eliminated

        return sorted(vals, key=lcv_score)

    def _is_consistent(self, var, val, assignment):
        temp = dict(assignment)
        temp[var] = val
        for clue_sum, run_cells in self.cell_to_clues[var]:
            vals = [temp[c] for c in run_cells if c in temp]
            if len(vals) != len(set(vals)):
                return False
            rem_count = len(run_cells) - len(vals)
            cur_sum = sum(vals)
            if rem_count == 0 and cur_sum != clue_sum:
                return False
            if rem_count > 0 and cur_sum >= clue_sum:
                return False
        return True

    def _backtrack(self, assignment, domains):
        if len(assignment) == len(self.white_cells):
            return assignment

        var = self._select_unassigned_var(assignment, domains)
        for val in self._order_domain_values(var, assignment, domains):
            self.explored_nodes += 1
            if not self._is_consistent(var, val, assignment):
                continue

            new_assign = dict(assignment)
            new_assign[var] = val
            new_domains = {c: set(d) for c, d in domains.items()}
            new_domains[var] = {val}

            ok = True
            if self.use_fc:
                for p in self.peers[var]:
                    if p not in new_assign and val in new_domains[p]:
                        new_domains[p].remove(val)
                        if not new_domains[p]:
                            ok = False
                            break

            if ok and self.use_prop:
                ok = self._propagate_sum_domains(new_domains, new_assign)

            if ok:
                res = self._backtrack(new_assign, new_domains)
                if res is not None:
                    return res

            self.backtracks += 1

        return None

    def solve(self):
        self.explored_nodes = 0
        self.backtracks = 0
        start_t = time.perf_counter()
        domains = self._initial_domains()
        sol = self._backtrack({}, domains)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return {
            "solution": sol,
            "nodes": self.explored_nodes,
            "backtracks": self.backtracks,
            "time_ms": elapsed_ms,
        }
