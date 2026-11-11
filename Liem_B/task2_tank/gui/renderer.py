import pygame


class GameRenderer:
    def __init__(self, screen, cell_size=48):
        self.screen = screen
        self.cs = cell_size
        self.font = pygame.font.SysFont("Arial", 13, bold=True)

    def _box3d(self, rect, top_c, side_c, depth=6, radius=4):
        pygame.draw.rect(self.screen, (10, 12, 16), rect.move(3, depth + 2), border_radius=radius)
        pygame.draw.rect(self.screen, side_c, rect.move(0, depth), border_radius=radius)
        top = rect.move(0, -2)
        pygame.draw.rect(self.screen, top_c, top, border_radius=radius)
        pygame.draw.rect(self.screen, (220, 225, 235), top, 1, border_radius=radius)
        return top

    def _hp_bar(self, x, y, w, hp, max_hp, col):
        pygame.draw.rect(self.screen, (15, 18, 22), (x, y, w, 5), border_radius=2)
        fw = int((w - 2) * max(0, min(hp, max_hp)) / max_hp)
        if fw > 0:
            pygame.draw.rect(self.screen, col, (x + 1, y + 1, fw, 3), border_radius=2)

    def _draw_tank(self, r, c, pid, tank, dir_delta):
        cs = self.cs
        cx, cy = c * cs + cs // 2, r * cs + cs // 2
        top_c, side_c, glow = ((50, 205, 105), (25, 115, 58), (90, 250, 140)) if pid == 1 else ((245, 145, 45), (150, 75, 18), (255, 190, 80))

        pygame.draw.circle(self.screen, (12, 14, 18), (cx + 3, cy + 4), cs // 2 - 6)
        vert = tank["dir"] in ("UP", "DOWN")
        # 2 banh xich
        for offset in (-15, 9):
            tr = pygame.Rect(cx + offset, cy - 14, 6, 28) if vert else pygame.Rect(cx - 14, cy + offset, 28, 6)
            pygame.draw.rect(self.screen, (42, 46, 54), tr, border_radius=2)

        # Than xe 3D + Thap phao vom cau + Nong sung
        hull = pygame.Rect(cx - 10, cy - 12, 20, 22) if vert else pygame.Rect(cx - 12, cy - 10, 24, 18)
        self._box3d(hull, top_c, side_c, depth=4, radius=4)

        dr, dc = dir_delta[tank["dir"]]
        end = (cx + dc * (cs // 2 - 3), cy - 3 + dr * (cs // 2 - 3))
        pygame.draw.line(self.screen, (215, 225, 235), (cx, cy - 3), end, 5)
        pygame.draw.circle(self.screen, side_c, (cx, cy - 1), 8)
        pygame.draw.circle(self.screen, glow, (cx, cy - 3), 7)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx - 2, cy - 5), 2)
        self._hp_bar(cx - 15, cy - 23, 30, tank["hp"], 6, glow)

    def draw(self, state):
        self.screen.fill((18, 22, 28))
        cs = self.cs

        # 1. Ve san + Painter's Algorithm theo tung hang tu tren xuong
        for r in range(state.rows):
            for c in range(state.cols):
                col = (30, 35, 44) if (r + c) % 2 == 0 else (26, 31, 39)
                pygame.draw.rect(self.screen, col, (c * cs + 1, r * cs + 1, cs - 2, cs - 2), border_radius=3)

                # Tuong 3D (doi mau + vet nut theo HP)
                if state.walls.get((r, c), 0) > 0:
                    hp = state.walls[(r, c)]
                    tc = (195, 115, 70) if hp == 3 else ((160, 90, 55) if hp == 2 else (125, 70, 48))
                    top = self._box3d(pygame.Rect(c * cs + 4, r * cs + 4, cs - 8, cs - 12), tc, (85, 45, 28), depth=6)
                    if hp < 3:
                        pygame.draw.line(self.screen, (30, 15, 10), top.topleft, top.center, 2)
                    if hp == 1:
                        pygame.draw.line(self.screen, (30, 15, 10), top.topright, top.bottomleft, 2)

                # Căn cứ (Base 3D)
                for pid, b in state.bases.items():
                    if b["hp"] > 0 and b["pos"] == (r, c):
                        tc, sc = ((45, 135, 230), (25, 75, 140)) if pid == 1 else ((225, 65, 70), (135, 30, 35))
                        top = self._box3d(pygame.Rect(c * cs + 4, r * cs + 4, cs - 8, cs - 12), tc, sc, depth=6, radius=6)
                        cx, cy = top.center
                        pygame.draw.polygon(self.screen, (255, 255, 255), [(cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy)])
                        self._hp_bar(c * cs + 6, r * cs - 4, cs - 12, b["hp"], 9, tc)

                # Xe tang (Tank 3D)
                for pid, t in state.tanks.items():
                    if t["hp"] > 0 and t["pos"] == (r, c):
                        self._draw_tank(r, c, pid, t, state.DIR_DELTA)

        # 2. Ve Dan bay lo lung (co bong tach roi)
        for b in state.bullets:
            cx, cy = b["pos"][1] * cs + cs // 2, b["pos"][0] * cs + cs // 2
            pygame.draw.circle(self.screen, (10, 12, 16), (cx + 3, cy + 6), 4)
            pygame.draw.circle(self.screen, (255, 200, 60), (cx, cy - 4), 6)
            pygame.draw.circle(self.screen, (255, 255, 255), (cx - 1, cy - 5), 2)

        # 3. Ve HUD 3D gon gang bang vong lap
        by = state.rows * cs
        w = self.screen.get_width()
        pygame.draw.line(self.screen, (70, 85, 110), (0, by), (w, by), 2)
        for pid, x, col in [(1, 10, (50, 205, 105)), (2, w - 195, (245, 145, 45))]:
            box = pygame.Rect(x, by + 8, 185, 58)
            pygame.draw.rect(self.screen, (26, 34, 46), box, border_radius=6)
            pygame.draw.rect(self.screen, col, box, 2, border_radius=6)
            t_hp, b_hp = max(0, state.tanks[pid]["hp"]), max(0, state.bases[pid]["hp"])
            self.screen.blit(self.font.render(f"P{pid} Tank:{t_hp}/6 Base:{b_hp}/9", True, (235, 240, 250)), (x + 10, by + 14))
            self._hp_bar(x + 10, by + 36, 165, t_hp, 6, col)
            self._hp_bar(x + 10, by + 48, 165, b_hp, 9, (70, 175, 255) if pid == 1 else (235, 80, 85))

        t_surf = self.font.render(f"TURN {state.turn}", True, (255, 215, 60))
        self.screen.blit(t_surf, (w // 2 - t_surf.get_width() // 2, by + 28))
        pygame.display.flip()