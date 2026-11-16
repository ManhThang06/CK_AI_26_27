"""Lan truyen rang buoc: dieu phoi cac Constraint (Run) tren Domains, co hoan tac."""
from .domains import Domains


class Propagator:
    """Moi phuong thuc tra ve (ok, removed); removed la list Removal. Khi that bai removed
    van chua cac gia tri da loai mot phan de nguoi goi hoan tac."""

    def __init__(self, runs):
        self.runs = list(runs)
        self.failed_run = None        # ten run gay that bai gan nhat
        self.runs_of = {}             # Cell -> cac run chua o do
        for run in self.runs:
            for cell in run.cells:
                self.runs_of.setdefault(cell, []).append(run)

    def initial_domains(self):
        return Domains.full(self.runs_of)

    def propagate_all(self, domains):
        # buoc dau: loc moi run, roi lan truyen toi diem co dinh
        return self._fixpoint(domains, list(self.runs), [])

    def assign(self, domains, cell, value):
        # gan cell = value roi loc hai run chua o do (va cac run bi anh huong)
        removed = []
        if value not in domains[cell]:
            return False, removed
        domains.fix(cell, value, removed)
        return self._fixpoint(domains, list(self.runs_of[cell]), removed)

    @staticmethod
    def undo(domains, removed):
        domains.restore(removed)

    def _fixpoint(self, domains, queue, removed):
        queue = list(queue)
        while queue:
            run = queue.pop()
            changed = run.filter(domains, removed)
            if changed is None:
                self.failed_run = run.name
                return False, removed
            for cell in changed:
                for other in self.runs_of[cell]:
                    if other is not run and other not in queue:
                        queue.append(other)
        return True, removed
