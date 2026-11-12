import math
import pygame

from CK_AI_26_27.Liem_B.task2_tank.engine import Direction

DIR_VEC = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
}

# Bảng màu Tactical 2.5D: (Màu chính, Màu giáp tối, Màu viền sáng, Màu neon phụ)
TANK_PALETTE = {
    0: {  # Tank 1 (MAX) - Emerald Cyber
        "main": (46, 204, 113),
        "dark": (24, 116, 64),
        "light": (130, 240, 175),
        "turret": (38, 175, 96),
        "glow": (80, 255, 160),
    },
    1: {  # Tank 2 (MIN) - Crimson Amber
        "main": (245, 130, 48),
        "dark": (145, 65, 15),
        "light": (255, 195, 130),
        "turret": (215, 105, 30),
        "glow": (255, 160, 60),
    },
}

BASE_PALETTE = {
    0: {"outer": (35, 115, 200), "inner": (85, 195, 255), "core": (210, 245, 255)},
    1: {"outer": (190, 45, 60), "inner": (255, 95, 110), "core": (255, 220, 225)},
}


class GameRenderer:
    """Renderer 2.5D Voxel & Tactical HUD cho Tank Battle (x = cot, y = hang)."""
    STATUS_H = 88

    def __init__(self, screen, cell_size, names=("Tank 1", "Tank 2")):
        self.screen = screen
        self.cs = cell_size
        self.names = names
        self.tick = 0
        self.font_sm = pygame.font.SysFont("Segoe UI", 11, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_hud = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 16, bold=True)

    @staticmethod
    def size_for(state, cell_size):
        return state.width * cell_size, state.height * cell_size + GameRenderer.STATUS_H

    def _draw_shadow(self, x, y, w, h, radius=6, alpha=95):
        """Vẽ bóng đổ mềm (Alpha Drop Shadow)."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 0, 0, alpha), (0, 0, w, h), border_radius=radius)
        self.screen.blit(surf, (x, y))

    def _draw_hp_bar(self, x, y, w, h, hp, max_hp, color_fg):
        """Vẽ thanh máu nhỏ nổi phía trên thực thể."""
        pygame.draw.rect(self.screen, (15, 18, 24), (x - 1, y - 1, w + 2, h + 2), border_radius=3)
        ratio = max(0.0, min(1.0, hp / float(max_hp)))
        fill_w = int(w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color_fg, (x, y, fill_w, h), border_radius=2)

    def _draw_floor(self, state):
        """Vẽ mặt sàn chiến trường kiểu gạch công nghiệp 2.5D."""
        cs, scr = self.cs, self.screen
        scr.fill((22, 26, 34))
        for y in range(state.height):
            for x in range(state.width):
                px, py = x * cs, y * cs
                # Màu ô bàn cờ lệch nhẹ tạo chiều sâu
                tile_color = (29, 34, 44) if (x + y) % 2 == 0 else (25, 30, 39)
                pygame.draw.rect(scr, tile_color, (px + 1, py + 1, cs - 2, cs - 2), border_radius=3)
                # Điểm đinh tán góc ô (Tactical grid dots)
                scr.set_at((px + 3, py + 3), (45, 52, 66))
                scr.set_at((px + cs - 4, py + cs - 4), (45, 52, 66))

    def _draw_walls(self, state):
        """Vẽ tường dạng khối hộp 3D có độ cao, vân gạch và vết nứt theo HP."""
        cs, scr = self.cs, self.screen
        for (x, y), hp in state.walls.items():
            px, py = x * cs, y * cs
            # Bóng đổ nghiêng xuống dưới-phải
            self._draw_shadow(px + 5, py + 6, cs - 4, cs - 4, radius=5, alpha=110)

            # Tường càng nhiều máu càng cao
            elev = 4 + hp * 2  # Độ dày vách trước
            if hp >= 3:
                top_c, front_c, border_c = (150, 125, 100), (100, 80, 62), (185, 160, 132)
            elif hp == 2:
                top_c, front_c, border_c = (128, 102, 82), (82, 64, 50), (155, 128, 105)
            else:
                top_c, front_c, border_c = (100, 75, 62), (65, 48, 38), (125, 96, 80)

            # Vách trước 3D (Mặt đứng tối màu)
            front_rect = pygame.Rect(px + 3, py + 6, cs - 6, cs - 8)
            pygame.draw.rect(scr, front_c, front_rect, border_radius=4)

            # Mặt đỉnh 3D (Nằm lệch lên trên để lộ vách trước)
            top_rect = pygame.Rect(px + 3, py + 6 - elev, cs - 6, cs - 8)
            pygame.draw.rect(scr, top_c, top_rect, border_radius=4)
            pygame.draw.rect(scr, border_c, top_rect, 1, border_radius=4)

            # Đường vân gạch ngang trên mặt đỉnh
            mid_y = top_rect.centery
            pygame.draw.line(scr, front_c, (top_rect.left + 3, mid_y), (top_rect.right - 3, mid_y), 1)

            # Vẽ vết nứt khi tường bị bắn (HP < 3)
            if hp <= 2:
                pygame.draw.line(scr, (45, 35, 30), (top_rect.left + 6, top_rect.top + 5), (top_rect.centerx, mid_y), 2)
            if hp == 1:
                pygame.draw.line(scr, (40, 28, 24), (top_rect.right - 6, top_rect.bottom - 5), (top_rect.centerx, mid_y), 2)

            # Huy hiệu HP nhỏ ở góc tường
            badge = pygame.Rect(top_rect.centerx - 8, top_rect.centery - 8, 16, 16)
            pygame.draw.rect(scr, (25, 25, 30), badge, border_radius=4)
            hp_surf = self.font_sm.render(str(hp), True, (240, 220, 180))
            scr.blit(hp_surf, (badge.centerx - hp_surf.get_width() // 2, badge.centery - hp_surf.get_height() // 2))

    def _draw_bases(self, state):
        """Vẽ Căn cứ dạng Boong-ke Lõi Năng lượng (Sci-Fi Command Center)."""
        cs, scr = self.cs, self.screen
        pulse = int(3 * math.sin(self.tick * 0.15))  # Hiệu ứng nhịp thở cho lõi căn cứ
        for i, b in enumerate(state.bases):
            if b.hp <= 0:
                continue
            px, py = b.x * cs, b.y * cs
            pal = BASE_PALETTE[i]

            # Bóng đổ
            self._draw_shadow(px + 5, py + 6, cs - 6, cs - 6, radius=8, alpha=120)

            # Đế kim loại (Metal platform)
            pygame.draw.rect(scr, (45, 52, 65), (px + 3, py + 5, cs - 6, cs - 6), border_radius=8)
            # Khối boong-ke nổi
            bunker_rect = pygame.Rect(px + 3, py + 2, cs - 6, cs - 8)
            pygame.draw.rect(scr, pal["outer"], bunker_rect, border_radius=8)
            pygame.draw.rect(scr, pal["inner"], bunker_rect, 2, border_radius=8)

            # 4 góc gia cố (Corner armor)
            for cx, cy in [
                (bunker_rect.left + 4, bunker_rect.top + 4),
                (bunker_rect.right - 6, bunker_rect.top + 4),
                (bunker_rect.left + 4, bunker_rect.bottom - 6),
                (bunker_rect.right - 6, bunker_rect.bottom - 6),
            ]:
                pygame.draw.rect(scr, (220, 230, 245), (cx, cy, 3, 3))

            # Lõi năng lượng phát sáng (Energy Core)
            cx, cy = bunker_rect.centerx, bunker_rect.centery
            pygame.draw.circle(scr, pal["inner"], (cx, cy), max(8, cs // 4 + pulse // 2))
            pygame.draw.circle(scr, pal["core"], (cx, cy), max(5, cs // 6))

            # Text HP trung tâm & Thanh máu
            txt = self.font_sm.render(f"B{i+1}:{b.hp}", True, (15, 20, 30))
            scr.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))
            self._draw_hp_bar(px + 6, py - 2, cs - 12, 4, b.hp, 9, pal["inner"])

    def _draw_tanks(self, state):
        """Vẽ Xe tăng 2.5D với bánh xích răng cưa, thân giáp, tháp pháo và nòng súng."""
        cs, scr = self.cs, self.screen
        for i, t in enumerate(state.tanks):
            if t.hp <= 0:
                continue
            px, py = t.x * cs, t.y * cs
            cx, cy = px + cs // 2, py + cs // 2 - 2
            pal = TANK_PALETTE[i]
            dx, dy = DIR_VEC[t.direction]

            # 1. Bóng đổ dưới mặt đất
            self._draw_shadow(px + 6, py + 7, cs - 10, cs - 10, radius=8, alpha=130)

            # 2. Bánh xích (Treads) xoay theo hướng di chuyển của xe
            if dx == 0:  # Đang quay LÊN hoặc XUỐNG -> Bánh xích nằm 2 bên Trái/Phải
                tread_l = pygame.Rect(px + 5, py + 5, 7, cs - 12)
                tread_r = pygame.Rect(px + cs - 12, py + 5, 7, cs - 12)
                for tr in (tread_l, tread_r):
                    pygame.draw.rect(scr, (32, 36, 42), tr, border_radius=3)
                    pygame.draw.rect(scr, (65, 72, 82), tr, 1, border_radius=3)
                    for ty in range(tr.top + 3, tr.bottom - 2, 5):
                        pygame.draw.line(scr, (85, 92, 105), (tr.left + 1, ty), (tr.right - 2, ty), 1)
                hull_rect = pygame.Rect(px + 10, py + 7, cs - 20, cs - 16)
            else:  # Đang quay TRÁI hoặc PHẢI -> Bánh xích nằm 2 bên Trên/Dưới
                tread_t = pygame.Rect(px + 5, py + 5, cs - 12, 7)
                tread_b = pygame.Rect(px + 5, py + cs - 14, cs - 12, 7)
                for tr in (tread_t, tread_b):
                    pygame.draw.rect(scr, (32, 36, 42), tr, border_radius=3)
                    pygame.draw.rect(scr, (65, 72, 82), tr, 1, border_radius=3)
                    for tx in range(tr.left + 3, tr.right - 2, 5):
                        pygame.draw.line(scr, (85, 92, 105), (tx, tr.top + 1), (tx, tr.bottom - 2), 1)
                hull_rect = pygame.Rect(px + 7, py + 10, cs - 16, cs - 20)

            # 3. Thân xe (Hull) 2 lớp sáng tối tạo khối 3D
            hull_shadow = hull_rect.move(0, 3)
            pygame.draw.rect(scr, pal["dark"], hull_shadow, border_radius=5)
            pygame.draw.rect(scr, pal["main"], hull_rect, border_radius=5)
            pygame.draw.rect(scr, pal["light"], hull_rect, 1, border_radius=5)

            # 4. Nòng pháo (Gun Barrel) + Bầu giảm giật (Mantlet) + Đầu nòng (Muzzle brake)
            barrel_len = cs // 2 - 2
            end_x, end_y = cx + dx * barrel_len, cy + dy * barrel_len
            # Bóng nòng pháo
            pygame.draw.line(scr, (20, 24, 30), (cx, cy + 2), (end_x, end_y + 2), 7)
            # Thân nòng kim loại
            pygame.draw.line(scr, (165, 175, 190), (cx, cy), (end_x, end_y), 5)
            pygame.draw.line(scr, (235, 240, 250), (cx, cy), (end_x, end_y), 2)
            # Đầu giảm giật ở mũi súng
            pygame.draw.circle(scr, (70, 80, 95), (end_x, end_y), 4)
            pygame.draw.circle(scr, pal["glow"], (end_x, end_y), 2)

            # 5. Tháp pháo (Turret) nổi ở tâm
            pygame.draw.circle(scr, pal["dark"], (cx, cy + 2), cs // 4 + 1)
            pygame.draw.circle(scr, pal["turret"], (cx, cy), cs // 4)
            pygame.draw.circle(scr, pal["light"], (cx, cy), cs // 4, 1)
            # Nắp tháp pháo (Commander hatch)
            pygame.draw.circle(scr, pal["dark"], (cx - 2, cy - 2), 4)
            pygame.draw.circle(scr, (240, 250, 255), (cx - 3, cy - 3), 2)

            # 6. Thanh máu (HP Bar) trên đầu xe tăng
            self._draw_hp_bar(px + 6, py - 3, cs - 12, 4, t.hp, 6, pal["glow"])

    def _draw_bullets(self, state):
        """Vẽ đạn Plasma có quầng sáng Alpha và đuôi lửa theo hướng bay."""
        cs, scr = self.cs, self.screen
        for b in state.bullets:
            cx, cy = b.x * cs + cs // 2, b.y * cs + cs // 2
            dx, dy = DIR_VEC.get(getattr(b, "direction", Direction.UP), (0, 0))

            # Vệt đuôi đạn (Trail) phía ngược chiều bay
            if dx != 0 or dy != 0:
                tail_x, tail_y = cx - dx * 12, cy - dy * 12
                pygame.draw.line(scr, (255, 100, 20), (cx, cy), (tail_x, tail_y), 5)
                pygame.draw.line(scr, (255, 210, 80), (cx, cy), (cx - dx * 7, cy - dy * 7), 3)

            # Quầng sáng Alpha xung quanh viên đạn
            glow = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 140, 0, 90), (12, 12), 10)
            pygame.draw.circle(glow, (255, 220, 60, 170), (12, 12), 6)
            scr.blit(glow, (cx - 12, cy - 12))
            pygame.draw.circle(scr, (255, 255, 240), (cx, cy), 3)

    def _draw_hud(self, state, message):
        """Vẽ bảng điều khiển chiến thuật (Tactical HUD) ở đáy màn hình."""
        cs, scr = self.cs, self.screen
        y0 = state.height * cs
        w = scr.get_width()

        # Nền HUD & đường viền kim loại
        pygame.draw.rect(scr, (16, 19, 26), (0, y0, w, self.STATUS_H))
        pygame.draw.line(scr, (55, 65, 85), (0, y0), (w, y0), 2)
        pygame.draw.line(scr, (90, 180, 255), (w // 3, y0), (2 * w // 3, y0), 2)

        t1, t2 = state.tanks[0], state.tanks[1]
        b1, b2 = state.bases[0], state.bases[1]
        active_p = state.player()

        # Thẻ thông tin Tank 1 (Trái) & Tank 2 (Phải)
        card_w = max(160, (w - 140) // 2)
        for idx, (tk, bs, x_pos) in enumerate([(t1, b1, 10), (t2, b2, w - card_w - 10)]):
            pal = TANK_PALETTE[idx]
            card = pygame.Rect(x_pos, y0 + 8, card_w, 44)
            bg_c = (26, 32, 44) if active_p == idx else (20, 24, 32)
            border_c = pal["glow"] if active_p == idx else (45, 52, 68)
            pygame.draw.rect(scr, bg_c, card, border_radius=6)
            pygame.draw.rect(scr, border_c, card, 2 if active_p == idx else 1, border_radius=6)

            # Chấm màu đại diện + Tên Agent
            pygame.draw.circle(scr, pal["main"], (card.left + 14, card.top + 14), 6)
            title = f"{self.names[idx][:18]}"
            scr.blit(self.font.render(title, True, (240, 245, 255)), (card.left + 26, card.top + 5))

            # Chỉ số HP Tank & HP Base
            stats = f"Tank HP: {tk.hp}/6   |   Base HP: {bs.hp}/9"
            scr.blit(self.font_sm.render(stats, True, pal["light"]), (card.left + 10, card.top + 24))

        # Khu vực trung tâm: Đồng hồ Cycle
        mid_x = w // 2
        cyc_txt = self.font_title.render(f"CYCLE {state.cycle}/{state.max_cycles}", True, (255, 215, 90))
        scr.blit(cyc_txt, (mid_x - cyc_txt.get_width() // 2, y0 + 10))

        # Thanh tiến độ Cycle ở giữa
        bar_w = 96
        bar_rect = pygame.Rect(mid_x - bar_w // 2, y0 + 34, bar_w, 6)
        pygame.draw.rect(scr, (35, 40, 52), bar_rect, border_radius=3)
        prog = min(1.0, state.cycle / float(max(1, state.max_cycles)))
        pygame.draw.rect(scr, (255, 200, 70), (bar_rect.x, bar_rect.y, int(bar_w * prog), 6), border_radius=3)

        # Dòng trạng thái / Log hành động ở dưới cùng
        msg_bar = pygame.Rect(10, y0 + 58, w - 20, 24)
        pygame.draw.rect(scr, (12, 15, 20), msg_bar, border_radius=4)
        msg_surf = self.font_hud.render(f"▸ {message}", True, (125, 225, 255))
        scr.blit(msg_surf, (msg_bar.left + 10, msg_bar.top + 2))

    def draw(self, state, message=""):
        self.tick += 1
        self._draw_floor(state)
        self._draw_walls(state)
        self._draw_bases(state)
        self._draw_tanks(state)
        self._draw_bullets(state)
        self._draw_hud(state, message)
        pygame.display.flip()