"""Co che nap agent ngoai (Task 2.3).

Hop dong: agent la lop co ham choose_action(state) tra ve Action (xem docs/interfaces.md).
Nap bang 1 trong 2 cach:
  - duong dan file .py        : "external_agents/my_agent.py"  (file tu chua du, hoac chi import task2_tank.*)
  - ten module + ten lop      : "algorithms.agents:AlphaBetaAgent"  (cho agent dung import tuong doi)
Agent loi / qua gio / tra ve hanh dong sai -> STAY, ghi log, game khong sap.
"""
import importlib
import importlib.util
import inspect
import os
import threading
import time

from CK_AI_26_27.Liem_B.task2_tank.engine import Action

DEFAULT_TIME_LIMIT = 1.0
MAX_STRIKES = 3          # so lan loi lien tiep truoc khi agent bi coi la hong


class AgentLoadError(Exception):
    pass


class SafeAgent:
    """Boc agent: chay trong thread co timeout, bat moi loi, ghi log."""

    def __init__(self, agent, time_limit=DEFAULT_TIME_LIMIT, log=None):
        self.agent = agent
        self.time_limit = time_limit
        self.log = log if log is not None else []
        self.name = getattr(agent, "name", agent.__class__.__name__)
        self.strikes = 0
        self.last_time = 0.0

    def _note(self, msg):
        line = "[%s] %s" % (self.name, msg)
        self.log.append(line)
        print(line)

    def choose_action(self, state):
        if self.strikes >= MAX_STRIKES:           # agent hong: khong goi nua
            return Action.STAY
        box = {}

        def run():
            try:
                box["action"] = self.agent.choose_action(state.clone())
            except BaseException as err:          # noqa: BLE001 - agent ngoai co the nem bat cu loi gi
                box["error"] = err

        t0 = time.perf_counter()
        th = threading.Thread(target=run, daemon=True)
        th.start()
        th.join(self.time_limit)
        self.last_time = time.perf_counter() - t0

        if th.is_alive():
            self.strikes += 1
            self._note("qua gio (> %.2fs) -> STAY (strike %d)" % (self.time_limit, self.strikes))
            return Action.STAY
        if "error" in box:
            self.strikes += 1
            self._note("loi %s: %s -> STAY (strike %d)" % (type(box["error"]).__name__, box["error"], self.strikes))
            return Action.STAY
        action = box.get("action")
        if not isinstance(action, Action):
            self.strikes += 1
            self._note("hanh dong khong hop le %r -> STAY (strike %d)" % (action, self.strikes))
            return Action.STAY
        self.strikes = 0
        return action

    # de GUI doc thong ke neu agent co bao cao
    @property
    def nodes(self):
        return getattr(self.agent, "nodes", None)


def _find_class(module, source_name):
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__ and callable(getattr(obj, "choose_action", None)) \
                and not inspect.isabstract(obj):
            return obj
    raise AgentLoadError("khong tim thay lop co choose_action() trong %s" % source_name)


def load_agent(spec, time_limit=DEFAULT_TIME_LIMIT, log=None, **kwargs):
    """spec: duong dan .py hoac 'module:Class'. Moi loi nap deu thanh AgentLoadError."""
    try:
        if ":" in spec and not os.path.exists(spec):
            mod_name, cls_name = spec.split(":", 1)
            cls = getattr(importlib.import_module(mod_name), cls_name)
        else:
            path = os.path.abspath(spec)
            if not os.path.isfile(path):
                raise AgentLoadError("khong tim thay file: %s" % path)
            name = "ext_agent_" + os.path.splitext(os.path.basename(path))[0]
            mspec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(mspec)
            mspec.loader.exec_module(module)
            cls = _find_class(module, path)
        agent = cls(**kwargs)
    except AgentLoadError:
        raise
    except BaseException as err:                  # noqa: BLE001
        raise AgentLoadError("khong nap duoc '%s': %s: %s" % (spec, type(err).__name__, err)) from err
    return SafeAgent(agent, time_limit, log)
