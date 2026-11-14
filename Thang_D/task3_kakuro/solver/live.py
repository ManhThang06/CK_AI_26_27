"""Chay solver trong thread rieng, UI lay tung su kien khi can (demand-driven).

Thread solver sinh su kien qua LiveRecorder. Sau moi su kien no kiem tra "han muc":
neu so su kien da sinh >= han muc thi cho. UI nang han muc (demand) khi nguoi dung
di toi su kien cuoi, nen thuat toan chi tiep tuc khi duoc yeu cau. UI chi doc danh sach
su kien (moi su kien la mot snapshot doc lap), khong cham vao trang thai cua solver.
"""
import sys
import threading

from .backtracking import BacktrackingSolver
from .heuristics import VARIABLE_SELECTORS, VALUE_ORDERERS
from .trace import TraceRecorder

TERMINAL = {"solution", "exhausted", "limit"}


class SearchAborted(Exception):
    """Nem ra trong thread solver khi UI huy phien."""


class LiveRecorder(TraceRecorder):
    def __init__(self, puzzle, stats, session):
        super().__init__(puzzle, stats)
        self.session = session

    def _emit(self, kind, *args, **kwargs):
        super()._emit(kind, *args, **kwargs)        # them su kien truoc khi cho
        self.session._after_emit(kind in TERMINAL)


class LiveSession:
    def __init__(self, puzzle, variable="mrv-degree", value="lcv", max_nodes=None):
        self.puzzle = puzzle
        self.solver = BacktrackingSolver(puzzle, VARIABLE_SELECTORS[variable](),
                                         VALUE_ORDERERS[value](), max_nodes=max_nodes)
        self.recorder = LiveRecorder(puzzle, self.solver.stats, self)
        self.solver.rec = self.recorder
        self.events = self.recorder.events           # list tang dan, UI chi doc
        self.meta = self.solver.config
        self.result = None
        self.error = None
        self._cond = threading.Condition()
        self._limit = 1                              # so su kien toi da duoc phep sinh
        self._stopped = False
        self._finished = False
        self._thread = None

    # ------------------------------------------------------------ phia UI
    @property
    def finished(self):
        """True khi su kien cuoi (solution/exhausted/limit) da duoc sinh, hoac solver loi."""
        return self._finished

    def start(self, timeout=10.0):
        """Chay thread va cho su kien dau tien (start)."""
        self._thread = threading.Thread(target=self._run, name="kakuro-solver", daemon=True)
        self._thread.start()
        with self._cond:
            self._cond.wait_for(lambda: self.events or self.error, timeout)
        if self.error:
            raise self.error
        if not self.events:
            raise TimeoutError("Solver khong sinh duoc su kien dau tien")

    def demand(self, count):
        """Cho phep solver sinh toi da `count` su kien (tinh tu dau)."""
        with self._cond:
            self._limit = max(self._limit, count)
            self._cond.notify_all()

    def finish(self):
        """Cho solver chay thang toi het."""
        self.demand(sys.maxsize)

    def stop(self):
        with self._cond:
            self._stopped = True
            self._cond.notify_all()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def wait_finished(self, timeout=30.0):
        if self._thread:
            self._thread.join(timeout)
        return self._finished

    # ------------------------------------------------------------ thread solver
    def _run(self):
        try:
            self.result = self.solver.solve()
        except SearchAborted:
            pass
        except Exception as exc:                     # bao loi cho UI thay vi treo
            self.error = exc
        finally:
            with self._cond:
                if not self._stopped:
                    self._finished = True
                self._cond.notify_all()

    def _after_emit(self, terminal):
        with self._cond:
            self._cond.notify_all()                  # bao cho UI co su kien moi
            if terminal:
                return
            while len(self.events) >= self._limit and not self._stopped:
                self._cond.wait()
            if self._stopped:
                raise SearchAborted()
