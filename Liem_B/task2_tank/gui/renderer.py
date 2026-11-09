import pygame


class GameRenderer:
    def __init__(self, screen, cell_size=48):
        self.screen = screen
        self.cell_size = cell_size
        self.font = pygame.font.SysFont("Arial", 16, bold=True)

    def draw(self, state):
        self.screen.fill((18, 18, 18))
        cs = self.cell_size

        # 1. Ve luoi ban do
        for r in range(state.rows):
            for c in range(state.cols):
                rect = pygame.Rect(c * cs, r * cs, cs, cs)
                pygame.draw.rect(self.screen, (38, 38, 38), rect, 1)

        # 2. Ve Tuong (Wall: max 3 HP, mau dam nhat theo HP)
        for (r, c), hp in state.walls.items():
            if hp > 0:
                shade = 90 + hp * 50
                rect = pygame.Rect(c * cs + 3, r * cs + 3, cs - 6, cs - 6)
                pygame.draw.rect(self.screen, (shade, shade - 30, 50), rect)
                hp_txt = self.font.render(str(hp), True, (0, 0, 0))
                self.screen.blit(hp_txt, (c * cs + cs // 2 - 5, r * cs + cs // 2 - 8))

        # 3. Ve Can cu (Base: 9 HP)
        for pid, base in state.bases.items():
            if base["hp"] > 0:
                r, c = base["pos"]
                color = (60, 160, 250) if pid == 1 else (240, 80, 80)
                rect = pygame.Rect(c * cs + 4, r * cs + 4, cs - 8, cs - 8)
                pygame.draw.rect(self.screen, color, rect, border_radius=6)
                txt = self.font.render(f"B{pid}:{base['hp']}", True, (255, 255, 255))
                self.screen.blit(txt, (c * cs + 6, r * cs + 14))

        # 4. Ve Xe tang (Tank: 6 HP) va nong sung theo huong nhin
        for pid, tank in state.tanks.items():
            if tank["hp"] > 0:
                r, c = tank["pos"]
                color = (50, 220, 100) if pid == 1 else (255, 160, 40)
                center = (c * cs + cs // 2, r * cs + cs // 2)
                pygame.draw.circle(self.screen, color, center, cs // 2 - 6)

                # Ve huong nong sung
                dr, dc = state.DIR_DELTA[tank["dir"]]
                end_pos = (center[0] + dc * (cs // 2), center[1] + dr * (cs // 2))
                pygame.draw.line(self.screen, (255, 255, 255), center, end_pos, 4)

                txt = self.font.render(f"T{pid}:{tank['hp']}", True, (0, 0, 0))
                self.screen.blit(txt, (c * cs + 8, r * cs + 14))

        # 5. Ve Dan (Bullet)
        for b in state.bullets:
            br, bc = b["pos"]
            center = (bc * cs + cs // 2, br * cs + cs // 2)
            pygame.draw.circle(self.screen, (255, 255, 100), center, 6)

        # 6. Ve thanh trang thai phia duoi
        info_y = state.rows * cs + 10
        status = (
            f"Turn: {state.turn} | "
            f"P1 (Tank:{state.tanks[1]['hp']}/6, Base:{state.bases[1]['hp']}/9) vs "
            f"P2 (Tank:{state.tanks[2]['hp']}/6, Base:{state.bases[2]['hp']}/9)"
        )
        surf = self.font.render(status, True, (240, 240, 240))
        self.screen.blit(surf, (15, info_y))
        pygame.display.flip()