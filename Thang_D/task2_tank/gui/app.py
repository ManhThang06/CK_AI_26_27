"""Cửa sổ pygame: menu chọn thuật toán và màn hình chơi.

Chạy:  python run_gui.py   (trong thư mục task2_tank)
"""

import threading
import time

import pygame

from ..engine import Action
from .agent_registry import build_registry
from .game_controller import GameController, HP_PRESETS, MAP_NAMES
from .renderer import Renderer, make_fonts, WIN_W, WIN_H, BG, TEXT, MUTED, PLAYER, PLAYER_LIGHT

P1_KEYS = {pygame.K_w: Action.MOVE_UP, pygame.K_s: Action.MOVE_DOWN,
           pygame.K_a: Action.MOVE_LEFT, pygame.K_d: Action.MOVE_RIGHT,
           pygame.K_SPACE: Action.FIRE, pygame.K_q: Action.STAY}
P2_KEYS = {pygame.K_UP: Action.MOVE_UP, pygame.K_DOWN: Action.MOVE_DOWN,
           pygame.K_LEFT: Action.MOVE_LEFT, pygame.K_RIGHT: Action.MOVE_RIGHT,
           pygame.K_RETURN: Action.FIRE, pygame.K_RSHIFT: Action.STAY}

ROW_W, ROW_H = 640, 46


class Menu:
    """Các dòng cấu hình; bấm nửa trái/phải của dòng (hoặc phím mũi tên) để đổi giá trị.

    Chế độ "same": cả hai tank dùng cùng một thuật toán (mỗi tank vẫn có agent riêng,
    mỗi agent tự mô phỏng cả MAX lẫn MIN trong cây tìm kiếm của nó).
    Chế độ "different": chọn thuật toán riêng cho từng tank (đấu thuật toán này với thuật toán khác).
    """

    MODES = ["Same algorithm for both tanks", "Different algorithm per tank"]

    def __init__(self, registry):
        self.registry = registry
        last = len(registry) - 1
        self.sel = {"mode": 0, "map": 1, "hp": 2, "p1": min(4, last), "d1": 1,
                    "p2": min(3, last), "d2": 1}
        self.focus = 0

    @property
    def same(self):
        return self.sel["mode"] == 0

    def rows(self):
        reg = self.registry
        rows = [("mode", "Mode", self.MODES[self.sel["mode"]], 2),
                ("map", "Map", MAP_NAMES[self.sel["map"]], len(MAP_NAMES)),
                ("hp", "HP preset", list(HP_PRESETS)[self.sel["hp"]], len(HP_PRESETS))]
        if self.same:
            rows += [("p1", "Algorithm", reg[self.sel["p1"]].label, len(reg)),
                     ("d1", "  Depth", self._depth_text("p1", "d1"), 4)]
        else:
            rows += [("p1", "Player 1 (blue)", reg[self.sel["p1"]].label, len(reg)),
                     ("d1", "  P1 depth", self._depth_text("p1", "d1"), 4),
                     ("p2", "Player 2 (red)", reg[self.sel["p2"]].label, len(reg)),
                     ("d2", "  P2 depth", self._depth_text("p2", "d2"), 4)]
        return rows

    def _depth_text(self, pkey, dkey):
        if not self.registry[self.sel[pkey]].uses_depth:
            return "n/a"
        return str(self.sel[dkey] + 1)

    def change(self, idx, step):
        rows = self.rows()
        key, _, _, n = rows[idx]
        if key in ("d1", "d2") and self._depth_text("p1" if key == "d1" else "p2", key) == "n/a":
            return
        self.sel[key] = (self.sel[key] + step) % n
        self.focus = min(self.focus, len(self.rows()) - 1)

    def build_controller(self):
        reg = self.registry
        pairs = (("p1", "d1"), ("p1", "d1")) if self.same else (("p1", "d1"), ("p2", "d2"))
        factories, labels = [], []
        for pkey, dkey in pairs:
            spec = reg[self.sel[pkey]]
            depth = min(self.sel[dkey] + 1, spec.max_depth)
            if spec.is_human:
                factories.append(None)
            else:
                factories.append(lambda s=spec, d=depth: s.factory(d))
            labels.append(spec.label + (" d=%d" % depth if spec.uses_depth else ""))
        return GameController(MAP_NAMES[self.sel["map"]], list(HP_PRESETS)[self.sel["hp"]],
                              factories, labels)


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tank Battle - Adversarial Search")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen, make_fonts())
        self.registry, self.plugin_errors = build_registry()
        self.menu = Menu(self.registry)
        self.mode = "menu"
        self.ctrl = None
        self.delay = 350          # ms chờ sau mỗi cycle
        self.paused = False
        self.step_once = False
        self.thinking = False
        self.pending_result = None
        self.token = 0
        self.next_time = 0.0

    # ------------------------------------------------------------ vòng lặp
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif self.mode == "menu":
                    self._menu_event(event)
                else:
                    self._game_event(event)
            if self.mode == "menu":
                self._draw_menu()
            else:
                self._update_game()
                self._draw_game()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    # ------------------------------------------------------------ menu
    def _row_rect(self, i):
        return pygame.Rect((WIN_W - ROW_W) // 2, 130 + i * (ROW_H + 8), ROW_W, ROW_H)

    def _button_rects(self):
        y = 130 + len(self.menu.rows()) * (ROW_H + 8) + 10
        x = (WIN_W - ROW_W) // 2
        return pygame.Rect(x, y, 400, 52), pygame.Rect(x + 420, y, 220, 52)

    def _menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            n = len(self.menu.rows())
            if event.key == pygame.K_UP:
                self.menu.focus = (self.menu.focus - 1) % n
            elif event.key == pygame.K_DOWN:
                self.menu.focus = (self.menu.focus + 1) % n
            elif event.key == pygame.K_LEFT:
                self.menu.change(self.menu.focus, -1)
            elif event.key == pygame.K_RIGHT:
                self.menu.change(self.menu.focus, 1)
            elif event.key == pygame.K_RETURN:
                self._start_game()
            elif event.key == pygame.K_F5:
                self._reload_plugins()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.menu.rows())):
                r = self._row_rect(i)
                if r.collidepoint(event.pos):
                    self.menu.focus = i
                    self.menu.change(i, -1 if event.pos[0] < r.centerx else 1)
            start, reload_ = self._button_rects()
            if start.collidepoint(event.pos):
                self._start_game()
            elif reload_.collidepoint(event.pos):
                self._reload_plugins()

    def _reload_plugins(self):
        self.registry, self.plugin_errors = build_registry()
        self.menu = Menu(self.registry)

    def _draw_menu(self):
        r = self.renderer
        self.screen.fill(BG)
        r.text("TANK BATTLE", "huge", TEXT, WIN_W // 2, 60, center=True)
        r.text("Choose a map and the algorithm for each tank", "body", MUTED, WIN_W // 2, 100, center=True)
        for i, (key, title, value, _) in enumerate(self.menu.rows()):
            rect = self._row_rect(i)
            focused = i == self.menu.focus
            pygame.draw.rect(self.screen, (44, 50, 64) if focused else (32, 36, 46), rect, border_radius=8)
            if not self.menu.same and key in ("p1", "d1"):
                pygame.draw.rect(self.screen, PLAYER[0], (rect.x, rect.y, 5, rect.height), border_radius=3)
            if not self.menu.same and key in ("p2", "d2"):
                pygame.draw.rect(self.screen, PLAYER[1], (rect.x, rect.y, 5, rect.height), border_radius=3)
            r.text(title, "body", MUTED, rect.x + 20, rect.centery - 9)
            r.text("<", "bold", MUTED, rect.x + 190, rect.centery - 10)
            r.text(value, "bold", TEXT, rect.x + 220, rect.centery - 10)
            r.text(">", "bold", MUTED, rect.right - 30, rect.centery - 10)
        start, reload_ = self._button_rects()
        pygame.draw.rect(self.screen, (60, 160, 100), start, border_radius=8)
        r.text("START  (Enter)", "bold", (10, 24, 16), start.centerx, start.centery, center=True)
        pygame.draw.rect(self.screen, (60, 66, 82), reload_, border_radius=8)
        r.text("Reload plugins (F5)", "body", TEXT, reload_.centerx, reload_.centery, center=True)
        y = reload_.bottom + 18
        extra = [s for s in self.registry if s.source == "plugin"]
        r.text("Plugins loaded: %d" % len(extra), "small", MUTED, (WIN_W - ROW_W) // 2, y)
        for fn, msg in self.plugin_errors[:3]:
            y += 18
            r.text("%s -> %s" % (fn, msg[:100]), "small", (255, 120, 100), (WIN_W - ROW_W) // 2, y)

    # ------------------------------------------------------------ ván chơi
    def _start_game(self):
        self.ctrl = self.menu.build_controller()
        self._reset_runtime()
        self.mode = "game"

    def _reset_runtime(self):
        self.token += 1
        self.thinking = False
        self.pending_result = None
        self.paused = False
        self.step_once = False
        self.next_time = 0.0

    def _game_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        if key == pygame.K_ESCAPE:
            self.token += 1
            self.mode = "menu"
        elif key == pygame.K_r:
            self.ctrl.reset()
            self._reset_runtime()
        elif key == pygame.K_p:
            self.paused = not self.paused
        elif key == pygame.K_n:
            self.paused = True
            self.step_once = True
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.delay = max(0, self.delay - 100)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.delay = min(2000, self.delay + 100)
        else:
            self._human_key(key)

    def _human_key(self, key):
        ctrl = self.ctrl
        if ctrl.is_over() or self.thinking:
            return
        p = ctrl.to_move
        if not ctrl.is_human(p):
            return
        both_maps = not (ctrl.is_human(0) and ctrl.is_human(1))
        keymap = {}
        if both_maps or p == 0:
            keymap.update(P1_KEYS)
        if both_maps or p == 1:
            keymap.update(P2_KEYS)
        if key in keymap:
            ctrl.apply(keymap[key])
            if ctrl.state.pending is None:
                self.next_time = time.monotonic() * 1000 + self.delay

    def _update_game(self):
        ctrl = self.ctrl
        if self.pending_result is not None:
            token, action = self.pending_result
            self.pending_result = None
            if token == self.token:
                self.thinking = False
                ctrl.apply(action)
                if ctrl.state.pending is None:
                    self.next_time = time.monotonic() * 1000 + self.delay
                    self.step_once = False
            return
        if ctrl.is_over() or self.thinking:
            return
        p = ctrl.to_move
        if ctrl.is_human(p):
            return
        mid_cycle = ctrl.state.pending is not None
        if not mid_cycle:
            if (self.paused and not self.step_once) or time.monotonic() * 1000 < self.next_time:
                return
        self._start_think(p)

    def _start_think(self, p):
        self.thinking = True
        token = self.token

        def work():
            try:
                action = self.ctrl.ai_action(p)
            except Exception:
                action = Action.STAY
            self.pending_result = (token, action)

        threading.Thread(target=work, daemon=True).start()

    def _draw_game(self):
        self.screen.fill(BG)
        now = time.monotonic() * 1000
        self.renderer.draw_board(self.ctrl, now)
        self.renderer.draw_panel(self.ctrl, {"thinking": self.thinking, "paused": self.paused,
                                             "delay": self.delay})
        if self.ctrl.is_over():
            self.renderer.draw_banner(self.ctrl.result_text())


def main():
    App().run()


if __name__ == "__main__":
    main()
