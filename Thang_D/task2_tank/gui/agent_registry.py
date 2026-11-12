"""Danh sách agent cho GUI: 4 thuật toán có sẵn, Human và agent nạp từ thư mục plugins/."""

import importlib.util
import inspect
import os
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from ..algorithms.agents import Agent, MinimaxAgent, AlphaBetaAgent
from ..algorithms.heuristic_search import (HeuristicMinimaxSearch,
                                           HeuristicAlphaBetaSearch)

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
MAX_PURE_HORIZON = 3   # Minimax thuần với horizon > 3 quá chậm để chơi realtime


class HeuristicAgent(Agent):
    """Bọc HeuristicMinimaxSearch / HeuristicAlphaBetaSearch.

    Mỗi bên giữ một đối tượng search riêng vì search nhớ các ô đã đứng (chống đi lòng vòng).
    """

    search_cls = None
    label = "Heuristic"

    def __init__(self, depth=2):
        self.depth = depth
        self.search = self.search_cls(depth=depth)
        self.last_result = None

    @property
    def name(self):
        return "%s (d=%d)" % (self.label, self.depth)

    def choose_action(self, state):
        self.last_result = self.search.search(state)
        return self.last_result.action


class HeuristicMinimaxAgent(HeuristicAgent):
    search_cls = HeuristicMinimaxSearch
    label = "Heuristic Minimax"


class HeuristicAlphaBetaAgent(HeuristicAgent):
    search_cls = HeuristicAlphaBetaSearch
    label = "Heuristic Alpha-Beta"


@dataclass
class AgentSpec:
    label: str
    factory: Optional[Callable]   # factory(depth) -> agent; None nghĩa là người chơi
    uses_depth: bool = False
    source: str = "built-in"      # built-in | plugin | human
    max_depth: int = 4            # độ sâu lớn nhất menu cho chọn

    @property
    def is_human(self):
        return self.factory is None


def _builtin_specs() -> List[AgentSpec]:
    return [
        AgentSpec("Human", None, False, "human"),
        AgentSpec("Minimax", lambda d: MinimaxAgent(horizon=min(d, MAX_PURE_HORIZON), move_ordering=True), True,
                  "built-in", MAX_PURE_HORIZON),
        AgentSpec("Alpha-Beta", lambda d: AlphaBetaAgent(horizon=d, move_ordering=True), True),
        AgentSpec("Heuristic Minimax", lambda d: HeuristicMinimaxAgent(depth=d), True),
        AgentSpec("Heuristic Alpha-Beta", lambda d: HeuristicAlphaBetaAgent(depth=d), True),
    ]


def _find_factory(module):
    """create_agent() nếu có, nếu không thì lớp đầu tiên định nghĩa trong module có choose_action()."""
    fn = getattr(module, "create_agent", None)
    if callable(fn):
        return fn
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if (cls.__module__ == module.__name__ and not inspect.isabstract(cls)
                and callable(getattr(cls, "choose_action", None))):
            return cls
    raise ValueError("không có create_agent() hoặc lớp nào có choose_action(state)")


def load_plugins(plugin_dir=PLUGIN_DIR) -> Tuple[List[AgentSpec], List[Tuple[str, str]]]:
    """Nạp mọi file .py trong plugin_dir (bỏ file bắt đầu bằng '_'). Trả về (specs, lỗi)."""
    specs, errors = [], []
    if not os.path.isdir(plugin_dir):
        return specs, errors
    for fn in sorted(os.listdir(plugin_dir)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        path = os.path.join(plugin_dir, fn)
        try:
            spec = importlib.util.spec_from_file_location("tank_plugin_" + fn[:-3], path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            factory = _find_factory(module)
            sample = factory()
            if not callable(getattr(sample, "choose_action", None)):
                raise ValueError("đối tượng trả về không có choose_action(state)")
            label = str(getattr(sample, "name", None) or fn[:-3])
        except Exception as exc:   # plugin hỏng không được làm sập GUI
            errors.append((fn, "%s: %s" % (type(exc).__name__, exc)))
            continue
        specs.append(AgentSpec(label + " [plugin]", lambda d, f=factory: f(), False, "plugin"))
    return specs, errors


def build_registry(plugin_dir=PLUGIN_DIR):
    specs, errors = load_plugins(plugin_dir)
    return _builtin_specs() + specs, errors
