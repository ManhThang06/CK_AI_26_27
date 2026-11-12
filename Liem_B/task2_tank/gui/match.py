"""Dieu khien mot van dau (khong phu thuoc pygame, nen test duoc).

Moi cycle gom 2 ply: MAX (tank 1) chon truoc, MIN (tank 2) chon sau - dung quy uoc cua C.
"""
import csv
import os
import time

from CK_AI_26_27.Liem_B.task2_tank.engine import GameMap, GameState


class Match:
    def __init__(self, map_path, agent_max, agent_min, max_cycles=None):
        gm = GameMap.load(map_path)
        self.state = GameState.from_map(gm) if max_cycles is None else GameState.from_map(gm, max_cycles)
        self.agents = (agent_max, agent_min)     # None = nguoi choi (GUI cung cap hanh dong)
        self.history = []                        # (cycle, who, action, thinking_time)

    def waiting_for_human(self):
        return self.agents[self.state.player()] is None

    def step(self, human_action=None):
        """Thuc hien 1 ply. Tra ve hanh dong da dung."""
        p = self.state.player()
        agent = self.agents[p]
        t0 = time.perf_counter()
        action = human_action if agent is None else agent.choose_action(self.state)
        dt = time.perf_counter() - t0
        self.history.append((self.state.cycle, "MAX" if p == 0 else "MIN", action.name, dt))
        self.state = self.state.result(action)
        return action

    def finished(self):
        return self.state.is_terminal()

    def result_text(self):
        u = self.state.utility()
        return {1: "Tank 1 (MAX) thang", -1: "Tank 2 (MIN) thang", 0: "Hoa"}[u]

    def save_log(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["cycle", "player", "action", "think_sec"])
            w.writerows(self.history)
            w.writerow([])
            w.writerow(["result", self.result_text(), "cycles", self.state.cycle])
