import copy
import pygame
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.plugin_loader import PluginLoader
from task2_tank.gui.menu import GameMenu
from task2_tank.gui.renderer import GameRenderer

class TankGameState:
    """Trang thai chuan cua Tank Battle theo dung quy tac de bai"""
    DIR_DELTA = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }
    def __init__(self, rows=11, cols=11):
        self.rows = rows
        self.cols = cols
        self.turn = 0
        # Tank: Initial HP = 6, Damage = 1
        self.tanks = {
            1: {"pos": (rows - 2, 1), "dir": "UP", "hp": 6},
            2: {"pos": (1, cols - 2), "dir": "DOWN", "hp": 6},
        }
        # Base: Initial HP = 9, Damage = 1
        self.bases = {
            1: {"pos": (rows - 1, cols // 2), "hp": 9},
            2: {"pos": (0, cols // 2), "hp": 9},
        }
        # Wall: Initial HP = 3, Damage = 1
        self.walls = {}
        for c in range(2, cols - 2):
            if c != cols // 2:
                self.walls[(rows // 2, c)] = 3
        self.walls[(rows - 2, cols // 2)] = 3
        self.walls[(1, cols // 2)] = 3

        self.bullets = []
    def clone(self):
        return copy.deepcopy(self)
    def is_terminal(self):
        for pid in (1, 2):
            if self.tanks[pid]["hp"] <= 0 or self.bases[pid]["hp"] <= 0:
                return True
        return False
    def get_winner(self):
        p1_alive = self.tanks[1]["hp"] > 0 and self.bases[1]["hp"] > 0
        p2_alive = self.tanks[2]["hp"] > 0 and self.bases[2]["hp"] > 0
        if p1_alive and not p2_alive:
            return 1
        if p2_alive and not p1_alive:
            return 2
        return 0
    def apply_action(self, player_id, action):
        tank = self.tanks[player_id]
        if tank["hp"] <= 0:
            return

        if action in ("MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"):
            direction = action.replace("MOVE_", "")
            tank["dir"] = direction
            dr, dc = self.DIR_DELTA[direction]
            nr, nc = tank["pos"][0] + dr, tank["pos"][1] + dc

            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                occupied = (
                    (nr, nc) in self.walls
                    or any(b["pos"] == (nr, nc) for b in self.bases.values())
                    or any(t["pos"] == (nr, nc) and t["hp"] > 0 for t in self.tanks.values())
                )
                if not occupied:
                    tank["pos"] = (nr, nc)

        elif action == "FIRE":
            self.bullets.append({
                "pos": tank["pos"],
                "dir": tank["dir"],
                "owner": player_id,
            })
    def update_bullets_cycle(self):
        """
        Moi chu ky game, dan bay toi da 3 o (speed = 3 cells/cycle).
        Xu ly tung o mot va kiem tra va cham ngay sau moi o.
        """
        active_bullets = []
        for b in self.bullets:
            dr, dc = self.DIR_DELTA[b["dir"]]
            hit = False
            for _ in range(3):
                nr, nc = b["pos"][0] + dr, b["pos"][1] + dc
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    hit = True
                    break

                b["pos"] = (nr, nc)

                # Kiem tra trung tuong (Wall)
                if (nr, nc) in self.walls:
                    self.walls[(nr, nc)] -= 1
                    if self.walls[(nr, nc)] <= 0:
                        del self.walls[(nr, nc)]
                    hit = True
                    break

                # Kiem tra trung Base
                for pid, base in self.bases.items():
                    if base["pos"] == (nr, nc) and base["hp"] > 0:
                        base["hp"] -= 1
                        hit = True
                        break
                if hit:
                    break

                # Kiem tra trung Tank
                for pid, tank in self.tanks.items():
                    if pid != b["owner"] and tank["pos"] == (nr, nc) and tank["hp"] > 0:
                        tank["hp"] -= 1
                        hit = True
                        break
                if hit:
                    break

            if not hit:
                active_bullets.append(b)

        self.bullets = active_bullets
        self.turn += 1
class SimpleBuiltinAgent(BaseAgent):
    """Agent mac dinh dung de test GUI khi chua nap file ngoai"""
    def get_action(self, state):
        my_tank = state.tanks[self.player_id]
        enemy_id = 2 if self.player_id == 1 else 1
        enemy_tank = state.tanks[enemy_id]

        mr, mc = my_tank["pos"]
        er, ec = enemy_tank["pos"]

        # Neu cung hang hoac cung cot voi xe tang dich thi ban
        if mr == er or mc == ec:
            return "FIRE"
        if mr > er:
            return "MOVE_UP"
        if mr < er:
            return "MOVE_DOWN"
        if mc > ec:
            return "MOVE_LEFT"
        return "MOVE_RIGHT"
class TankBattleApp:
    def __init__(self):
        pygame.init()
        self.cell_size = 48
        self.rows = 11
        self.cols = 11
        width = self.cols * self.cell_size
        height = self.rows * self.cell_size + 45
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("TDTU AI - Tank Battle")

    def _resolve_agent(self, spec_str, player_id):
        if spec_str == "Built-in Heuristic Agent":
            return SimpleBuiltinAgent(player_id=player_id)
        return PluginLoader.load_agent_from_file(spec_str, player_id=player_id)
    def _get_human_action(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        return "MOVE_UP"
                    if event.key == pygame.K_DOWN:
                        return "MOVE_DOWN"
                    if event.key == pygame.K_LEFT:
                        return "MOVE_LEFT"
                    if event.key == pygame.K_RIGHT:
                        return "MOVE_RIGHT"
                    if event.key == pygame.K_SPACE:
                        return "FIRE"
                    if event.key == pygame.K_s:
                        return "STAY"
    def run(self):
        menu = GameMenu(self.screen)
        config = menu.run()
        if config is None:
            pygame.quit()
            return
        state = TankGameState(self.rows, self.cols)
        renderer = GameRenderer(self.screen, self.cell_size)

        agent1 = None if config["mode"] == "Player vs Agent" else self._resolve_agent(config["p1_agent"], 1)
        agent2 = self._resolve_agent(config["p2_agent"], 2)

        clock = pygame.time.Clock()
        running = True

        while running and not state.is_terminal():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            renderer.draw(state)

            # Lay hanh dong cua Player 1
            if agent1 is None:
                act1 = self._get_human_action()
                if act1 == "QUIT":
                    break
            else:
                act1 = agent1.get_action(state)

            # Lay hanh dong cua Player 2
            act2 = agent2.get_action(state)

            state.apply_action(1, act1)
            state.apply_action(2, act2)
            state.update_bullets_cycle()

            renderer.draw(state)
            clock.tick(4)

        winner = state.get_winner()
        print(f"Game ket thuc! Nguoi chien thang: Player {winner}")
        pygame.time.wait(2000)
        pygame.quit()
if __name__ == "__main__":
    app = TankBattleApp()
    app.run()