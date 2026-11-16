"""Danh sách agent cho GUI: 4 thuật toán có sẵn, Human và agent nạp từ thư mục plugins/."""

import importlib.util
import inspect
import os
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from ..algorithms.agents import (MinimaxAgent, AlphaBetaAgent,
                                 HeuristicMinimaxAgent, HeuristicAlphaBetaAgent)

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")


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
        # randomize + horizon_score: với HP chuẩn 6/9/3, horizon nông không thấy thắng/thua nên mọi nước đều
        # bằng điểm; nếu cứ lấy nước đầu tiên thì tank đâm đầu vào tường (MOVE_UP) mãi. Xem AdversarialSearch.
        AgentSpec("Minimax", lambda d: MinimaxAgent(horizon=d, move_ordering=True,
                                                    randomize=True, horizon_score=True, time_limit=0.5, tactical_ties=True), True,
                  "built-in", 4),
        AgentSpec("Alpha-Beta", lambda d: AlphaBetaAgent(horizon=d, move_ordering=True,
                                                         randomize=True, horizon_score=True, time_limit=0.5, tactical_ties=True), True),
        AgentSpec("Heuristic Minimax", lambda d: HeuristicMinimaxAgent(depth=d, time_limit=0.5), True),
        AgentSpec("Heuristic Alpha-Beta", lambda d: HeuristicAlphaBetaAgent(depth=d, time_limit=0.5), True),
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
