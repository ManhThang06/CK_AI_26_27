import time
from task2_tank.engine import GameMap, GameState, Action

def big_state():
    rows = ["A" + "." * 11 + "B"]
    for y in range(1, 12):
        rows.append("".join("#" if (x + y) % 3 == 0 and 2 < x < 10 else "." for x in range(13)))
    rows[6] = "1" + rows[6][1:-1] + "2"
    return GameState.from_map(GameMap.parse("\n".join(rows)))

def per_call_us(fn, n):
    start = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - start) / n * 1e6

if __name__ == "__main__":
    s = big_state()
    mid = s.result(Action.FIRE)          
    print("walls:", len(s.walls))
    print("clone          : %.2f us" % per_call_us(s.clone, 100000))
    print("result (MAX)   : %.2f us" % per_call_us(lambda: s.result(Action.STAY), 100000))
    print("result (cycle) : %.2f us" % per_call_us(lambda: mid.result(Action.FIRE), 50000))
