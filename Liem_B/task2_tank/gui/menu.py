import os
import pygame


class GameMenu:
    def __init__(self, screen, agents_dir="external_agents"):
        self.screen = screen
        self.agents_dir = agents_dir
        self.f_title = pygame.font.SysFont("Arial", 26, bold=True)
        self.f_item = pygame.font.SysFont("Arial", 16, bold=True)
        self.modes = ["Agent vs Agent", "Player vs Agent"]
        self.mode_idx = 0
        self.agent_files = self._scan_agents()
        self.p1_idx = 0
        self.p2_idx = min(1, len(self.agent_files) - 1) if self.agent_files else 0
        self.sel = 0

    def _scan_agents(self):
        files = ["Built-in Heuristic Agent"]
        if os.path.isdir(self.agents_dir):
            files += [os.path.join(self.agents_dir, f) for f in sorted(os.listdir(self.agents_dir))
                      if f.endswith(".py") and not f.startswith("__")]
        return files

    def _box3d(self, rect, top_c, side_c, border_c, depth=5):
        pygame.draw.rect(self.screen, (10, 12, 16), rect.move(4, depth + 3), border_radius=8)
        pygame.draw.rect(self.screen, side_c, rect.move(0, depth), border_radius=8)
        pygame.draw.rect(self.screen, top_c, rect, border_radius=8)
        pygame.draw.rect(self.screen, border_c, rect, 2, border_radius=8)

    def _shift(self, row, step):
        if row == 0:
            self.mode_idx = (self.mode_idx + step) % len(self.modes)
        elif row == 1 and self.agent_files:
            self.p1_idx = (self.p1_idx + step) % len(self.agent_files)
        elif row == 2 and self.agent_files:
            self.p2_idx = (self.p2_idx + step) % len(self.agent_files)

    def run(self):
        clock = pygame.time.Clock()
        w, _ = self.screen.get_size()
        while True:
            self.screen.fill((18, 22, 28))
            self._box3d(pygame.Rect(35, 25, w - 70, 60), (32, 40, 54), (18, 24, 34), (255, 195, 40))
            t_surf = self.f_title.render("TANK BATTLE - 3D ARENA", True, (255, 215, 60))
            self.screen.blit(t_surf, (w // 2 - t_surf.get_width() // 2, 40))

            p1 = "Human (Arrows+Space)" if self.modes[self.mode_idx] == "Player vs Agent" else os.path.basename(self.agent_files[self.p1_idx])
            p2 = os.path.basename(self.agent_files[self.p2_idx])
            items = [
                f"Mode [M]:  < {self.modes[self.mode_idx]} >",
                f"Tank 1 [Q]:  < {p1} >",
                f"Tank 2 [W]:  < {p2} >",
                "BAT DAU TRAN DAU (ENTER / SPACE)",
            ]

            for i, text in enumerate(items):
                active = (i == self.sel)
                r = pygame.Rect(40, 115 + i * 82, w - 80, 62)
                tc = (40, 135, 75) if i == 3 and active else ((44, 54, 72) if active else (30, 36, 48))
                bc = (120, 255, 160) if i == 3 and active else ((90, 200, 255) if active else (55, 65, 82))
                self._box3d(r, tc, (20, 25, 34), bc)
                self.screen.blit(self.f_item.render(text, True, (255, 255, 255) if active else (190, 195, 205)), (r.x + 18, r.y + 20))

            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE: return None
                    elif ev.key == pygame.K_UP: self.sel = (self.sel - 1) % 4
                    elif ev.key == pygame.K_DOWN: self.sel = (self.sel + 1) % 4
                    elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT): self._shift(self.sel, 1 if ev.key == pygame.K_RIGHT else -1)
                    elif ev.key == pygame.K_m: self._shift(0, 1)
                    elif ev.key == pygame.K_q: self._shift(1, 1)
                    elif ev.key == pygame.K_w: self._shift(2, 1)
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return {"mode": self.modes[self.mode_idx], "p1_agent": self.agent_files[self.p1_idx], "p2_agent": self.agent_files[self.p2_idx]}
            clock.tick(30)