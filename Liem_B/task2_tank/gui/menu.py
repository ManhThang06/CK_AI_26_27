import os
import pygame


class GameMenu:
    def __init__(self, screen, agents_dir="external_agents"):
        self.screen = screen
        self.agents_dir = agents_dir
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_item = pygame.font.SysFont("Arial", 20)

        self.modes = ["Agent vs Agent", "Player vs Agent"]
        self.mode_idx = 0

        self.agent_files = self._scan_agents()
        self.p1_agent_idx = 0
        self.p2_agent_idx = min(1, len(self.agent_files) - 1) if self.agent_files else 0

    def _scan_agents(self):
        files = ["Built-in Heuristic Agent"]
        if os.path.isdir(self.agents_dir):
            for fname in sorted(os.listdir(self.agents_dir)):
                if fname.endswith(".py") and not fname.startswith("__"):
                    files.append(os.path.join(self.agents_dir, fname))
        return files

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.screen.fill((25, 28, 35))
            title = self.font_title.render("TANK BATTLE - AI ARENA", True, (255, 215, 0))
            self.screen.blit(title, (140, 50))

            lines = [
                f"[1] Che do choi (Phim M): {self.modes[self.mode_idx]}",
                f"[2] Agent Tank 1 (Phim Q): {os.path.basename(self.agent_files[self.p1_agent_idx])}",
                f"[3] Agent Tank 2 (Phim W): {os.path.basename(self.agent_files[self.p2_agent_idx])}",
                "",
                "Nhan ENTER hoac SPACE de bat dau tran dau",
                "Nhan ESC de thoat",
            ]

            for i, text in enumerate(lines):
                color = (220, 220, 220) if i < 3 else (120, 230, 140)
                surf = self.font_item.render(text, True, color)
                self.screen.blit(surf, (80, 140 + i * 45))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_m:
                        self.mode_idx = (self.mode_idx + 1) % len(self.modes)
                    elif event.key == pygame.K_q and self.agent_files:
                        self.p1_agent_idx = (self.p1_agent_idx + 1) % len(self.agent_files)
                    elif event.key == pygame.K_w and self.agent_files:
                        self.p2_agent_idx = (self.p2_agent_idx + 1) % len(self.agent_files)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return {
                            "mode": self.modes[self.mode_idx],
                            "p1_agent": self.agent_files[self.p1_agent_idx],
                            "p2_agent": self.agent_files[self.p2_agent_idx],
                        }
            clock.tick(30)