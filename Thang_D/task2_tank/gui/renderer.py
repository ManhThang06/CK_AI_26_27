"""Vẽ bàn chơi và bảng thông tin bằng pygame."""

import pygame

WIN_W, WIN_H = 1120, 720
PANEL_W = 360

BG = (22, 24, 30)
CELL_A = (34, 37, 46)
CELL_B = (38, 42, 52)
TEXT = (230, 232, 238)
MUTED = (140, 146, 160)
WALL_FULL = (150, 104, 66)
WALL_LOW = (92, 66, 48)
PLAYER = [(70, 140, 245), (235, 85, 75)]
PLAYER_LIGHT = [(160, 200, 255), (255, 170, 160)]
BULLET = [(190, 225, 255), (255, 205, 190)]
FLASH = {"wall": (255, 190, 90), "tank": (255, 90, 60), "base": (255, 240, 120)}
HP_BAR_BG = (60, 64, 76)
GOOD = (90, 200, 120)


def make_fonts():
    names = "arial,dejavusans,helvetica,liberationsans"
    return {
        "small": pygame.font.SysFont(names, 14),
        "body": pygame.font.SysFont(names, 17),
        "bold": pygame.font.SysFont(names, 18, bold=True),
        "title": pygame.font.SysFont(names, 30, bold=True),
        "huge": pygame.font.SysFont(names, 44, bold=True),
    }


def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


class Renderer:
    FLASH_MS = 450

    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts

    # ------------------------------------------------------------ tiện ích
    def text(self, s, font, color, x, y, center=False):
        surf = self.fonts[font].render(s, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def bar(self, x, y, w, h, ratio, color):
        pygame.draw.rect(self.screen, HP_BAR_BG, (x, y, w, h), border_radius=3)
        ratio = max(0.0, min(1.0, ratio))
        if ratio > 0:
            pygame.draw.rect(self.screen, color, (x, y, max(2, int(w * ratio)), h), border_radius=3)

    # ------------------------------------------------------------ bàn chơi
    def draw_board(self, ctrl, now_ms):
        st = ctrl.state
        area_w = WIN_W - PANEL_W
        cell = min((area_w - 40) // st.width, (WIN_H - 40) // st.height)
        ox = (area_w - cell * st.width) // 2
        oy = (WIN_H - cell * st.height) // 2

        def rect_of(x, y):
            return pygame.Rect(ox + x * cell, oy + y * cell, cell, cell)

        for y in range(st.height):
            for x in range(st.width):
                pygame.draw.rect(self.screen, CELL_A if (x + y) % 2 == 0 else CELL_B, rect_of(x, y))

        for (x, y), hp in st.walls.items():
            r = rect_of(x, y).inflate(-4, -4)
            color = lerp(WALL_LOW, WALL_FULL, hp / max(1, ctrl.max_wall_hp))
            pygame.draw.rect(self.screen, color, r, border_radius=4)
            self.text(str(hp), "small", (40, 28, 20), r.centerx, r.centery, center=True)

        for i, b in enumerate(st.bases):
            r = rect_of(b.x, b.y).inflate(-6, -6)
            alive = b.hp > 0
            pygame.draw.rect(self.screen, PLAYER[i] if alive else (70, 70, 74), r, border_radius=6)
            pygame.draw.rect(self.screen, PLAYER_LIGHT[i], r, 3, border_radius=6)
            self.text("B%d" % (i + 1), "bold", (15, 15, 20), r.centerx, r.centery, center=True)
            self._hp_bar(rect_of(b.x, b.y), b.hp / ctrl.max_base_hp)

        for i, t in enumerate(st.tanks):
            self._draw_tank(rect_of(t.x, t.y), t, i, ctrl.max_tank_hp)

        for bl in st.bullets:
            r = rect_of(bl.x, bl.y)
            pygame.draw.circle(self.screen, BULLET[bl.owner], r.center, max(3, cell // 8))

        for (x, y, kind) in ctrl.events:
            age = now_ms - ctrl.events_time
            if age < self.FLASH_MS:
                frac = age / self.FLASH_MS
                r = rect_of(x, y)
                size = int(cell * (0.5 + frac))
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = int(200 * (1 - frac))
                pygame.draw.circle(surf, FLASH[kind] + (alpha,), (size // 2, size // 2), size // 2)
                self.screen.blit(surf, surf.get_rect(center=r.center))

    def _hp_bar(self, cell_rect, ratio):
        self.bar(cell_rect.x + 4, cell_rect.y + 2, cell_rect.width - 8, 4, ratio, GOOD)

    def _draw_tank(self, cell_rect, tank, idx, max_hp):
        alive = tank.hp > 0
        body = cell_rect.inflate(-int(cell_rect.width * 0.32), -int(cell_rect.height * 0.32))
        color = PLAYER[idx] if alive else (80, 80, 84)
        pygame.draw.rect(self.screen, color, body, border_radius=5)
        dx, dy = tank.direction.value
        cx, cy = body.center
        length = cell_rect.width * 0.48
        end = (cx + dx * length, cy + dy * length)
        pygame.draw.line(self.screen, PLAYER_LIGHT[idx] if alive else (110, 110, 114),
                         (cx, cy), end, max(4, cell_rect.width // 9))
        self.text("P%d" % (idx + 1), "small", (12, 12, 18), cx, cy, center=True)
        self._hp_bar(cell_rect, tank.hp / max_hp)

    # ------------------------------------------------------------ bảng thông tin
    def draw_panel(self, ctrl, ui):
        x0 = WIN_W - PANEL_W
        pygame.draw.rect(self.screen, (28, 31, 39), (x0, 0, PANEL_W, WIN_H))
        pad = x0 + 20
        y = 18
        self.text("TANK BATTLE", "title", TEXT, pad, y)
        y += 44
        self.text("Map: %s   HP: %s" % (ctrl.map_name, ctrl.hp_preset), "small", MUTED, pad, y)
        y += 20
        self.text("Cycle %d / 100" % ctrl.state.cycle, "bold", TEXT, pad, y)
        y += 34

        st = ctrl.state
        for i in (0, 1):
            tag = "Human" if ctrl.is_human(i) else ctrl.labels[i]
            self.text("P%d  %s" % (i + 1, tag), "bold", PLAYER_LIGHT[i], pad, y)
            y += 24
            self.text("Tank", "small", MUTED, pad, y)
            self.bar(pad + 44, y + 3, 150, 10, st.tanks[i].hp / ctrl.max_tank_hp, PLAYER[i])
            self.text("%d/%d" % (max(0, st.tanks[i].hp), ctrl.max_tank_hp), "small", TEXT, pad + 204, y)
            y += 20
            self.text("Base", "small", MUTED, pad, y)
            self.bar(pad + 44, y + 3, 150, 10, st.bases[i].hp / ctrl.max_base_hp, PLAYER[i])
            self.text("%d/%d" % (max(0, st.bases[i].hp), ctrl.max_base_hp), "small", TEXT, pad + 204, y)
            y += 20
            agent = ctrl.agents[i]
            last = ctrl.last_actions[i].name if ctrl.last_actions[i] else "-"
            info = "last: %s" % last
            if agent is not None:
                info += "   think: %.0f ms" % (agent.last_time * 1000)
                if agent.last_nodes is not None:
                    info += "   nodes: %d" % agent.last_nodes
            self.text(info, "small", MUTED, pad, y)
            y += 18
            if agent is not None and agent.last_error:
                self.text("ERROR: " + agent.last_error[:46], "small", (255, 120, 100), pad, y)
            y += 22

        y += 4
        if ctrl.is_over():
            self.text(ctrl.result_text(), "bold", (255, 220, 110), pad, y)
        elif ui["thinking"]:
            self.text("P%d is thinking..." % (ctrl.to_move + 1), "body", (255, 220, 110), pad, y)
        elif ctrl.is_human(ctrl.to_move):
            self.text("Waiting for P%d key press" % (ctrl.to_move + 1), "body", (255, 220, 110), pad, y)
        elif ui["paused"]:
            self.text("Paused", "body", (255, 220, 110), pad, y)
        y += 30

        self.text("Recent cycles", "small", MUTED, pad, y)
        y += 18
        for line in list(ctrl.log)[-8:]:
            self.text(line, "small", TEXT, pad, y)
            y += 16

        y = WIN_H - 128
        for line in ("P pause   N step   +/- speed (%d ms)" % ui["delay"],
                     "R restart   ESC menu",
                     "P1 keys: W A S D, SPACE fire, Q stay",
                     "P2 keys: arrows, ENTER fire, RSHIFT stay"):
            self.text(line, "small", MUTED, pad, y)
            y += 20

    def draw_banner(self, text):
        area_w = WIN_W - PANEL_W
        surf = pygame.Surface((area_w, 90), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 170))
        self.screen.blit(surf, (0, WIN_H // 2 - 45))
        self.text(text, "huge", (255, 225, 120), area_w // 2, WIN_H // 2, center=True)
