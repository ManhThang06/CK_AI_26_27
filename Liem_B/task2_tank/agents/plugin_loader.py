import importlib.util
import inspect
import os
import time
from task2_tank.agents.base_agent import BaseAgent, VALID_ACTIONS


class SafeAgentWrapper:
    def __init__(self, agent_instance, time_limit_sec=1.0):
        self.agent = agent_instance
        self.time_limit_sec = time_limit_sec
        self.name = getattr(agent_instance, "name", agent_instance.__class__.__name__)

    def get_action(self, state):
        # Truyen ban sao state de ngan agent ben ngoai lam thay doi trang thai that
        safe_state = state.clone() if hasattr(state, "clone") else state
        start_t = time.perf_counter()

        try:
            action = self.agent.get_action(safe_state)
        except Exception as err:
            print(f"[Plugin Warning] Agent {self.name} gap loi: {err} -> Chuyen thanh STAY")
            return "STAY"

        elapsed = time.perf_counter() - start_t
        if elapsed > self.time_limit_sec:
            print(f"[Plugin Timeout] Agent {self.name} chay {elapsed:.3f}s (> {self.time_limit_sec}s) -> Phạt STAY")
            return "STAY"

        if action not in VALID_ACTIONS:
            print(f"[Plugin Invalid] Hanh dong '{action}' khong hop le -> Chuyen thanh STAY")
            return "STAY"

        return action


class PluginLoader:
    @staticmethod
    def load_agent_from_file(file_path, player_id, time_limit_sec=1.0):
        norm_path = os.path.abspath(file_path)
        if not os.path.isfile(norm_path):
            raise FileNotFoundError(f"Khong tim thay file agent: {norm_path}")

        module_name = "ext_agent_" + os.path.splitext(os.path.basename(norm_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, norm_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Khong the tao spec cho file: {norm_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        target_class = None
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is BaseAgent or obj.__module__ != module.__name__:
                continue
            if issubclass(obj, BaseAgent) or hasattr(obj, "get_action"):
                target_class = obj
                break

        if target_class is None:
            raise ValueError(f"Khong tim thay class Agent hop le trong {norm_path}")

        try:
            instance = target_class(player_id=player_id)
        except TypeError:
            instance = target_class()
            instance.player_id = player_id

        return SafeAgentWrapper(instance, time_limit_sec=time_limit_sec)