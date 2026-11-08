# Experiment harness for task 2.2: every configuration plays the same scenarios
# against the same opponent with the same seeds, and each game is one CSV row.
import csv
import time

from task2_tank.engine import GameMap, GameState

COLUMNS = ["scenario", "config", "game", "seed", "result", "cycles", "moves",
           "time_total_s", "time_mean_s", "time_max_s", "nodes_mean", "depth_mean"]


class Scenario:
    def __init__(self, name, map_path, max_cycles):
        self.name = name
        self.map_path = map_path
        self.max_cycles = max_cycles

    def new_state(self):
        return GameState.from_map(GameMap.load(self.map_path), self.max_cycles)


def play_game(agent_max, agent_min, state):
    # agent_max is the agent under test; only its moves are measured
    times, nodes, depths = [], [], []
    agents = [agent_max, agent_min]
    while not state.is_terminal():
        agent = agents[state.player()]
        agent.reset_stats()
        start = time.perf_counter()
        action = agent.choose_action(state)
        elapsed = time.perf_counter() - start
        if agent is agent_max:
            times.append(elapsed)
            nodes.append(agent.nodes)
            depths.append(agent.last_depth)
        state = state.result(action)
    n = max(len(times), 1)
    return {
        "result": state.utility(), "cycles": state.cycle, "moves": len(times),
        "time_total_s": sum(times), "time_mean_s": sum(times) / n,
        "time_max_s": max(times, default=0.0),
        "nodes_mean": sum(nodes) / n, "depth_mean": sum(depths) / n,
    }


def run_experiment(scenarios, configs, opponent, games, out_csv, base_seed=0):
    # configs: {name: make_agent()}; opponent: make_agent(seed)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for scenario in scenarios:
            for config, make_agent in configs.items():
                for g in range(games):
                    seed = base_seed + g
                    row = play_game(make_agent(), opponent(seed), scenario.new_state())
                    row.update(scenario=scenario.name, config=config, game=g, seed=seed)
                    writer.writerow(row)
