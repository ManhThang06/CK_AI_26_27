"""Chạy thử một ván trong console, dùng engine của team.

Chạy từ thư mục chứa task2_tank:
    python -m task2_tank.play_demo --map small --horizon 2
"""

import argparse

from .algorithms import MinimaxAgent, AlphaBetaAgent, play_match
from .algorithms.agents import RandomAgent
from .algorithms.scenarios import load_state


def build_agent(kind, horizon, ordering, seed):
    if kind == "minimax":
        return MinimaxAgent(horizon=horizon, move_ordering=ordering,
                            randomize=True, horizon_score=True, seed=seed,
                            time_limit=0.5, tactical_ties=True)
    if kind == "alphabeta":
        return AlphaBetaAgent(horizon=horizon, move_ordering=ordering,
                              randomize=True, horizon_score=True, seed=seed,
                              time_limit=0.5, tactical_ties=True)
    if kind == "heuristic":
        from .algorithms.agents import HeuristicMinimaxAgent
        return HeuristicMinimaxAgent(depth=horizon, time_limit=0.5)
    if kind == "heuristic-ab":
        from .algorithms.agents import HeuristicAlphaBetaAgent
        return HeuristicAlphaBetaAgent(depth=horizon, time_limit=0.5)
    return RandomAgent(seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", choices=["small", "medium", "full"], default="small")
    ap.add_argument("--horizon", type=int, default=2)
    ap.add_argument("--max-agent", choices=["minimax", "alphabeta", "heuristic", "heuristic-ab", "random"], default="alphabeta")
    ap.add_argument("--min-agent", choices=["minimax", "alphabeta", "heuristic", "heuristic-ab", "random"], default="random")
    ap.add_argument("--ordering", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    state = load_state(args.map)
    a_max = build_agent(args.max_agent, args.horizon, args.ordering, args.seed)
    a_min = build_agent(args.min_agent, args.horizon, args.ordering, args.seed + 1)
    print("MAX:", a_max.name, "| MIN:", a_min.name)
    final, utility, t_max, t_min = play_match(state, a_max, a_min, verbose=True)
    result = {1: "MAX thắng", 0: "hòa", -1: "MIN thắng"}[utility]
    print("Kết quả: %s sau %d cycle (suy nghĩ: MAX %.2fs, MIN %.2fs)" % (result, final.cycle, t_max, t_min))


if __name__ == "__main__":
    main()
