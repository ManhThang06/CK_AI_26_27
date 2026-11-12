"""Heuristic cho Backtracking: chon bien (MRV, Degree) va sap xep gia tri (LCV).

Mot o duoc coi la "chua gan" khi mien con tu 2 gia tri tro len. O co mien 1 gia tri
da duoc xac dinh (do gan hoac do propagation) nen khong can chon nua.
Cac ham o day lam viec voi o dang tuple (r, c) cua tang model.
"""
from abc import ABC, abstractmethod

from ..model.propagation import Propagator

INF = float("inf")


def unassigned(domains):
    return [c for c, d in domains.items() if len(d) > 1]


def degree(cell, domains, prop):
    """So o chua gan cung run voi `cell` (cac rang buoc Alldiff/Sum dang noi chung)."""
    peers = {x for run in prop.runs_of[cell] for x in run.cells if x != cell}
    return sum(1 for x in peers if len(domains[x]) > 1)


# ------------------------------------------------------------------ chon bien
class VariableSelector(ABC):
    name = ""

    @abstractmethod
    def select(self, domains, prop):
        """Tra ve o tiep theo can gan, hoac None neu tat ca da xac dinh."""

    def describe(self, cell, domains, prop):
        return self.name


class FirstUnassigned(VariableSelector):
    """Baseline: o chua gan dau tien theo thu tu hang, cot."""
    name = "first"

    def select(self, domains, prop):
        free = unassigned(domains)
        return min(free) if free else None


class MRV(VariableSelector):
    """Minimum Remaining Values: o co mien nho nhat. Hoa thi lay o dau theo hang, cot."""
    name = "mrv"

    def select(self, domains, prop):
        free = unassigned(domains)
        if not free:
            return None
        return min(free, key=lambda c: (len(domains[c]), c))

    def describe(self, cell, domains, prop):
        return f"MRV |D|={len(domains[cell])}"


class MRVDegree(MRV):
    """MRV, hoa thi chon o co Degree lon nhat (rang buoc nhieu o chua gan nhat)."""
    name = "mrv-degree"

    def select(self, domains, prop):
        free = unassigned(domains)
        if not free:
            return None
        return min(free, key=lambda c: (len(domains[c]), -degree(c, domains, prop), c))

    def describe(self, cell, domains, prop):
        return f"MRV |D|={len(domains[cell])}, Degree={degree(cell, domains, prop)}"


# ------------------------------------------------------------------ sap xep gia tri
class ValueOrderer(ABC):
    name = ""

    @abstractmethod
    def order(self, cell, domains, prop):
        """Tra ve list (gia tri, diem). Gia tri dung truoc se duoc thu truoc."""

    def describe(self, score):
        return ""


class AscendingOrder(ValueOrderer):
    name = "asc"

    def order(self, cell, domains, prop):
        return [(v, None) for v in sorted(domains[cell])]


class LCV(ValueOrderer):
    """Least Constraining Value.

    Voi moi gia tri v, thu gan cell = v bang Propagator.assign roi dem so gia tri bi loai
    khoi mien cac o khac (gom ca phan lan truyen qua tong cua run), sau do hoan tac.
    Gia tri loai it nhat duoc thu truoc. Gia tri dan toi mau thuan co diem vo cung lon
    nen bi xep cuoi.
    """
    name = "lcv"

    def order(self, cell, domains, prop):
        scored = []
        for v in sorted(domains[cell]):
            ok, removed = prop.assign(domains, cell, v)
            cost = sum(1 for c, _, _ in removed if c != cell) if ok else INF
            Propagator.undo(domains, removed)
            scored.append((v, cost))
        scored.sort(key=lambda t: (t[1], t[0]))     # hoa thi gia tri nho truoc
        return scored

    def describe(self, score):
        return "LCV dead end" if score == INF else f"LCV cost={score}"


VARIABLE_SELECTORS = {cls.name: cls for cls in (FirstUnassigned, MRV, MRVDegree)}
VALUE_ORDERERS = {cls.name: cls for cls in (AscendingOrder, LCV)}
