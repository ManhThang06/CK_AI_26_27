"""Vẽ bàn chơi, HUD và menu bằng pygame, theo phong cách tối giản như ảnh mẫu:
nền xanh đen, tường cam nổi khối, căn cứ kim cương (P1 xanh dương, P2 đỏ),
tank xanh lá (P1) / cam (P2), thanh HUD ở cuối cửa sổ.
"""

import math

import pygame

MENU_SIZE = (720, 660)
MIN_GAME_W = 720
HUD_H = 132
MAX_CELL = 64

# ------------------------------------------------------------------ màu
BG = (17, 19, 25)
GRID = (22, 25, 32)
CELL_A = (30, 33, 42)
CELL_B = (34, 38, 48)
TEXT = (232, 234, 240)
MUTED = (126, 134, 150)
GOLD = (255, 200, 40)

WALL_TOP = (201, 117, 78)
WALL_SIDE = (143, 78, 48)
WALL_RIM = (245, 214, 190)
WALL_DEAD = (96, 62, 46)

TANK = [(52, 199, 89), (255, 159, 28)]          # P1 xanh lá, P2 cam
TANK_DARK = [(30, 130, 58), (186, 108, 12)]
BASE = [(41, 121, 255), (229, 57, 53)]          # P1 xanh dương, P2 đỏ
BASE_DARK = [(24, 78, 176), (150, 32, 30)]
DEAD = (84, 86, 94)
HP_BG = (58, 62, 74)
HP_OK = (88, 214, 110)
HP_WARN = (255, 214, 64)
HP_BAD = (255, 90, 70)

FLASH = {"wall": (255, 190, 90), "tank": (255, 90, 60), "base": (255, 240, 120)}

MOVE_MS = 200      # thời gian trượt của tank
BULLET_MS = 300    # thời gian bay của đạn
FLASH_MS = 450


def make_fonts():
    names = "segoeui,arial,dejavusans,helvetica,liberationsans"
    return {
        "tiny": pygame.font.SysFont(names, 12),
        "small": pygame.font.SysFont(names, 14),
        "body": pygame.font.SysFont(names, 17),
        "bold": pygame.font.SysFont(names, 17, bold=True),
        "hud": pygame.font.SysFont(names, 16, bold=True),
        "turn": pygame.font.SysFont(names, 20, bold=True),
        "title": pygame.font.SysFont(names, 40, bold=True),
        "huge": pygame.font.SysFont(names, 48, bold=True),
    }


def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def clamp01(v):
    return max(0.0, min(1.0, v))


def ease(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def cell_size(cols, rows):
    return max(28, min(MAX_CELL, 700 // max(cols, 1), 620 // max(rows, 1)))


def game_window_size(cols, rows):
    c = cell_size(cols, rows)
    return max(MIN_GAME_W, c * cols), c * rows + HUD_H


class Renderer:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts

    # ------------------------------------------------------------ tiện ích
    def text(self, s, font, color, x, y, center=False, right=False):
        surf = self.fonts[font].render(s, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        elif right:
            rect.topright = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def bar(self, x, y, w, h, ratio, color, bg=HP_BG):
        pygame.draw.rect(self.screen, bg, (x, y, w, h), border_radius=h // 2)
        ratio = clamp01(ratio)
        if ratio > 0:
            pygame.draw.rect(self.screen, color, (x, y, max(h, int(w * ratio)), h), border_radius=h // 2)

    def glow(self, center, radius, color, alpha):
        size = int(radius * 2)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, color + (alpha,), (size // 2, size // 2), size // 2)
        self.screen.blit(surf, surf.get_rect(center=center))

    # ------------------------------------------------------------ bàn chơi
    def board_geometry(self, ctrl):
        st = ctrl.state
        cell = cell_size(st.width, st.height)
        w = self.screen.get_width()
        ox = (w - cell * st.width) // 2
        return cell, ox, 0

    def draw_board(self, ctrl, now_ms):
        st = ctrl.state
        cell, ox, oy = self.board_geometry(ctrl)
        board = pygame.Rect(ox, oy, cell * st.width, cell * st.height)
        pygame.draw.rect(self.screen, GRID, board)

        def rect_of(x, y):
            return pygame.Rect(ox + int(x * cell), oy + int(y * cell), cell, cell)

        def center_of(x, y):
            return (ox + (x + 0.5) * cell, oy + (y + 0.5) * cell)

        for y in range(st.height):
            for x in range(st.width):
                col = CELL_A if (x + y) % 2 == 0 else CELL_B
                pygame.draw.rect(self.screen, col, rect_of(x, y).inflate(-2, -2), border_radius=3)

        for (x, y), hp in st.walls.items():
            self._draw_wall(rect_of(x, y), hp / max(1, ctrl.max_wall_hp))

        for i, b in enumerate(st.bases):
            self._draw_base(rect_of(b.x, b.y), i, b.hp, ctrl.max_base_hp)

        age = now_ms - ctrl.events_time
        tween_t = ease(age / MOVE_MS) if ctrl.prev_state is not None else 1.0
        for i, t in enumerate(st.tanks):
            tx, ty = float(t.x), float(t.y)
            if ctrl.prev_state is not None and tween_t < 1.0:
                p = ctrl.prev_state.tanks[i]
                tx = p.x + (t.x - p.x) * tween_t
                ty = p.y + (t.y - p.y) * tween_t
            self._draw_tank(pygame.Rect(ox + int(tx * cell), oy + int(ty * cell), cell, cell),
                            t, i, ctrl.max_tank_hp)

        bt = ease(age / BULLET_MS)
        for bl in st.bullets:
            dx, dy = bl.direction.value
            # Đạn còn sống sau cycle đã bay đúng 3 ô, nên vị trí đầu cycle là lùi 3 ô.
            sx, sy = bl.x - 3 * dx, bl.y - 3 * dy
            fx = sx + (bl.x - sx) * bt
            fy = sy + (bl.y - sy) * bt
            self._draw_bullet(center_of(fx, fy), (dx, dy), bl.owner, cell, bt < 1.0)

        for (x, y, kind) in ctrl.events:
            a = now_ms - ctrl.events_time - BULLET_MS * 0.4   # nổ khi đạn tới nơi
            if 0 <= a < FLASH_MS:
                frac = a / FLASH_MS
                r = rect_of(x, y)
                size = int(cell * (0.5 + frac))
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = int(210 * (1 - frac))
                pygame.draw.circle(surf, FLASH[kind] + (alpha,), (size // 2, size // 2), size // 2)
                self.screen.blit(surf, surf.get_rect(center=r.center))

    def _draw_wall(self, cell_rect, ratio):
        r = cell_rect.inflate(-int(cell_rect.width * 0.14), -int(cell_rect.height * 0.14))
        r.height -= 3
        depth = max(3, cell_rect.height // 12)
        top = lerp(WALL_DEAD, WALL_TOP, clamp01(ratio))
        side = lerp((60, 40, 32), WALL_SIDE, clamp01(ratio))
        pygame.draw.rect(self.screen, side, r.move(0, depth), border_radius=6)
        pygame.draw.rect(self.screen, top, r, border_radius=6)
        pygame.draw.rect(self.screen, lerp(top, WALL_RIM, 0.75), r, 1, border_radius=6)
        if ratio < 0.99:   # vết nứt khi tường bị bắn
            cx, cy = r.center
            cracks = 1 if ratio > 0.5 else 2
            col = lerp(top, (40, 22, 16), 0.7)
            pygame.draw.lines(self.screen, col, False,
                              [(cx - r.w // 4, cy - r.h // 3), (cx, cy - 2), (cx - 3, cy + r.h // 5),
                               (cx + r.w // 6, cy + r.h // 3)], 2)
            if cracks == 2:
                pygame.draw.lines(self.screen, col, False,
                                  [(cx + r.w // 3, cy - r.h // 4), (cx + 2, cy + 2), (cx + r.w // 4, cy + r.h // 4)], 2)

    def _draw_base(self, cell_rect, i, hp, max_hp):
        alive = hp > 0
        r = cell_rect.inflate(-int(cell_rect.width * 0.14), -int(cell_rect.height * 0.14))
        r.height -= 3
        depth = max(3, cell_rect.height // 12)
        main = BASE[i] if alive else DEAD
        dark = BASE_DARK[i] if alive else (56, 58, 64)
        pygame.draw.rect(self.screen, dark, r.move(0, depth), border_radius=6)
        pygame.draw.rect(self.screen, main, r, border_radius=6)
        pygame.draw.rect(self.screen, lerp(main, (255, 255, 255), 0.7), r, 1, border_radius=6)
        cx, cy = r.center
        d = r.width * 0.2
        pygame.draw.polygon(self.screen, (255, 255, 255) if alive else (150, 150, 156),
                            [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)])
        self._thin_hp(cell_rect, hp / max_hp, BASE[i], y_off=1)

    def _thin_hp(self, cell_rect, ratio, color, y_off=0):
        w = int(cell_rect.width * 0.6)
        x = cell_rect.centerx - w // 2
        y = cell_rect.y + y_off + 1
        self.bar(x, y, w, 4, ratio, color if ratio > 0 else HP_BG)

    def _draw_tank(self, cell_rect, tank, idx, max_hp):
        alive = tank.hp > 0
        c = cell_rect.width
        cx, cy = cell_rect.center
        # bóng đổ
        self.glow((cx + c * 0.06, cy + c * 0.08), c * 0.46, (0, 0, 0), 120)
        body = pygame.Rect(0, 0, int(c * 0.58), int(c * 0.58))
        body.center = (cx, cy)
        main = TANK[idx] if alive else DEAD
        dark = TANK_DARK[idx] if alive else (60, 62, 68)
        dx, dy = tank.direction.value
        # nòng súng
        end = (cx + dx * c * 0.46, cy + dy * c * 0.46)
        pygame.draw.line(self.screen, lerp(main, (255, 255, 255), 0.35), (cx, cy), end, max(4, c // 10))
        pygame.draw.rect(self.screen, dark, body.move(0, 2), border_radius=7)
        pygame.draw.rect(self.screen, main, body, border_radius=7)
        pygame.draw.circle(self.screen, lerp(main, (255, 255, 255), 0.85) if alive else (140, 140, 146),
                           (cx, cy), max(4, int(c * 0.14)))
        ratio = tank.hp / max_hp
        self._thin_hp(cell_rect, ratio, HP_OK if ratio > 0.5 else HP_WARN if ratio > 0.25 else HP_BAD,
                      y_off=-1)

    def _draw_bullet(self, center, direction, owner, cell, flying):
        col = TANK[owner]
        dx, dy = direction
        if flying:
            tail = (center[0] - dx * cell * 0.6, center[1] - dy * cell * 0.6)
            pygame.draw.line(self.screen, lerp(col, BG, 0.45), tail, center, max(2, cell // 14))
        self.glow(center, cell * 0.22, col, 90)
        pygame.draw.circle(self.screen, lerp(col, (255, 255, 255), 0.7), center, max(3, cell // 11))

    # ------------------------------------------------------------ HUD
    def draw_hud(self, ctrl, ui):
        w, h = self.screen.get_size()
        y0 = h - HUD_H
        pygame.draw.rect(self.screen, (12, 14, 19), (0, y0, w, HUD_H))
        pygame.draw.line(self.screen, (44, 48, 60), (0, y0), (w, y0), 2)

        center_w = 130
        gap = 14
        box_w = (w - center_w - gap * 4) // 2
        box_h = 92
        by = y0 + 12
        boxes = [pygame.Rect(gap, by, box_w, box_h),
                 pygame.Rect(w - gap - box_w, by, box_w, box_h)]
        st = ctrl.state
        active = ctrl.to_move if not ctrl.is_over() else -1
        for i, box in enumerate(boxes):
            self._player_box(ctrl, i, box, active == i)

        # giữa: lượt + trạng thái
        mid = w // 2
        self.text("TURN %d" % st.cycle, "turn", GOLD, mid, by + 24, center=True)
        if ctrl.is_over():
            status, col = ctrl.result_text(), GOLD
        elif ui["thinking"]:
            status, col = "P%d thinking..." % (ctrl.to_move + 1), TEXT
        elif ctrl.is_human(ctrl.to_move):
            status, col = "P%d: your move" % (ctrl.to_move + 1), TEXT
        elif ui["paused"]:
            status, col = "Paused", TEXT
        else:
            status, col = "%d / 100" % st.cycle, MUTED
        self.text(status, "small", col, mid, by + 52, center=True)
        self.text("map: %s" % ctrl.map_name, "tiny", MUTED, mid, by + 74,
                  center=True)

        hint = ("P pause · N step · +/- speed (%d ms) · R restart · ESC menu    "
                "P1: WASD, SPACE fire, Q stay   P2: arrows, ENTER fire, RSHIFT stay" % ui["delay"])
        self.text(hint, "tiny", MUTED, mid, h - 14, center=True)

    def _player_box(self, ctrl, i, box, is_active):
        st = ctrl.state
        edge = TANK[i]
        fill = (20, 28, 26) if i == 0 else (31, 25, 20)
        pygame.draw.rect(self.screen, fill, box, border_radius=9)
        pygame.draw.rect(self.screen, edge if is_active or ctrl.is_over() else lerp(edge, fill, 0.5),
                         box, 2, border_radius=9)
        px = box.x + 12
        tank, base = st.tanks[i], st.bases[i]
        self.text("P%d  Tank:%d/%d  Base:%d/%d" % (i + 1, max(0, tank.hp), ctrl.max_tank_hp,
                                                   max(0, base.hp), ctrl.max_base_hp),
                  "hud", TEXT, px, box.y + 8)
        bw = box.width - 24
        self.bar(px, box.y + 34, bw, 5, tank.hp / ctrl.max_tank_hp, TANK[i])
        self.bar(px, box.y + 45, bw, 5, base.hp / ctrl.max_base_hp, BASE[i])
        agent = ctrl.agents[i]
        if agent is None:
            info = "Human"
        else:
            info = ctrl.labels[i]
            if agent.last_time:
                info += "  ·  %.0f ms" % (agent.last_time * 1000)
            if agent.last_nodes is not None:
                info += "  ·  %d nodes" % agent.last_nodes
        last = ctrl.last_actions[i].name if ctrl.last_actions[i] else "-"
        self.text(info, "tiny", MUTED, px, box.y + 58)
        if agent is not None and agent.last_error:
            self.text("ERROR: " + agent.last_error[:40], "tiny", HP_BAD, px, box.y + 74)
        else:
            self.text("last: %s" % last, "tiny", MUTED, px, box.y + 74)

    def draw_banner(self, text, board_w):
        w = self.screen.get_width()
        h = self.screen.get_height() - HUD_H
        surf = pygame.Surface((w, 90), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 175))
        self.screen.blit(surf, (0, h // 2 - 45))
        self.text(text, "huge", GOLD, w // 2, h // 2, center=True)

    # ------------------------------------------------------------ menu
    def draw_menu_row(self, rect, title, value, focused, accent=None):
        pygame.draw.rect(self.screen, (36, 41, 54) if focused else (26, 29, 38), rect, border_radius=10)
        if focused:
            pygame.draw.rect(self.screen, (84, 96, 124), rect, 1, border_radius=10)
        if accent:
            pygame.draw.rect(self.screen, accent, (rect.x, rect.y + 8, 5, rect.height - 16), border_radius=3)
        self.text(title, "body", MUTED, rect.x + 22, rect.centery - 10)
        self.text("<", "bold", MUTED, rect.x + 220, rect.centery - 10)
        self.text(value, "bold", TEXT, rect.x + 250, rect.centery - 10)
        self.text(">", "bold", MUTED, rect.right - 30, rect.centery - 10)

    def draw_menu_logo(self, cx, y):
        """Hình trang trí: căn cứ - tank - tường, cùng bảng màu với bàn chơi."""
        cell = 44
        x0 = cx - cell * 2
        for k in range(5):
            r = pygame.Rect(x0 + k * cell, y, cell, cell)
            pygame.draw.rect(self.screen, CELL_A if k % 2 == 0 else CELL_B, r.inflate(-2, -2), border_radius=3)
        self._draw_base(pygame.Rect(x0, y, cell, cell), 0, 1, 1)
        self._draw_wall(pygame.Rect(x0 + cell, y, cell, cell), 1.0)
        self._draw_tank(pygame.Rect(x0 + 2 * cell, y, cell, cell), _FakeTank(0), 0, 1)
        self._draw_wall(pygame.Rect(x0 + 3 * cell, y, cell, cell), 1.0)
        self._draw_base(pygame.Rect(x0 + 4 * cell, y, cell, cell), 1, 1, 1)


class _FakeTank:
    class _D:
        value = (1, 0)

    def __init__(self, hp):
        self.hp = 1
        self.direction = self._D()
