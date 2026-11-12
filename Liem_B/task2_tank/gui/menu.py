import os
import pygame

from CK_AI_26_27.Liem_B.task2_tank.plugin_loader import load_agent
from CK_AI_26_27.Liem_B.task2_tank.agents.builtin import RandomAgent, ChaserAgent

BUILTIN = {"Built-in: Chaser": ChaserAgent, "Built-in: Random": RandomAgent}
HUMAN = "Human (Arrow Keys + SPACE, S = Stay)"


class GameMenu:
    """Menu chon ban do va agent voi giao dien Tactical Card UI."""

    def __init__(self, screen, base_dir):
        self.screen = screen
        self.base = base_dir
        self.font_title = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_key = pygame.font.SysFont("Consolas", 15, bold=True)

        self.maps = sorted(f for f in os.listdir(os.path.join(base_dir, "maps")) if f.endswith(".txt"))
        ext_dir = os.path.join(base_dir, "external_agents")
        self.ext = [
            os.path.join(ext_dir, f)
            for f in sorted(os.listdir(ext_dir))
            if f.endswith(".py") and not f.startswith("__")
        ] if os.path.isdir(ext_dir) else []
        self.options = [HUMAN] + list(BUILTIN) + self.ext
        self.sel = [1, min(2, len(self.options) - 1), 0]  # agent1, agent2, map

    def label(self, spec):
        return spec if spec in BUILTIN or spec == HUMAN else "External: " + os.path.basename(spec)

    def build(self, spec, log):
        if spec == HUMAN:
            return None
        if spec in BUILTIN:
            return load_agent_builtin(spec)
        return load_agent(spec, log=log)

    def _draw_card(self, y, key_char, title, value, accent_color):
        """Vẽ từng thẻ lựa chọn có bóng đổ 3D và nút phím tắt."""
        scr = self.screen
        w = scr.get_width()
        card = pygame.Rect(32, y, w - 64, 52)
        # Bóng đổ dưới thẻ
        pygame.draw.rect(scr, (10, 12, 18), card.move(3, 4), border_radius=8)
        # Thân thẻ
        pygame.draw.rect(scr, (30, 36, 48), card, border_radius=8)
        pygame.draw.rect(scr, (55, 65, 85), card, 1, border_radius=8)
        # Thanh màu nhấn bên trái
        pygame.draw.rect(scr, accent_color, (card.left, card.top, 6, card.height), border_radius=4)

        # Nút phím tắt [Q], [W], [M]
        key_box = pygame.Rect(card.left + 18, card.centery - 14, 32, 28)
        pygame.draw.rect(scr, (18, 22, 30), key_box, border_radius=5)
        pygame.draw.rect(scr, accent_color, key_box, 1, border_radius=5)
        k_surf = self.font_key.render(key_char, True, accent_color)
        scr.blit(k_surf, (key_box.centerx - k_surf.get_width() // 2, key_box.centery - k_surf.get_height() // 2))

        # Nhãn & Giá trị đang chọn
        lbl_surf = self.font_sub.render(title.upper(), True, (150, 165, 190))
        val_surf = self.font.render(str(value), True, (240, 245, 255))
        scr.blit(lbl_surf, (card.left + 62, card.top + 6))
        scr.blit(val_surf, (card.left + 62, card.top + 24))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            scr = self.screen
            w, h = scr.get_size()
            scr.fill((18, 22, 30))

            # Vẽ lưới nền trang trí
            for gx in range(0, w, 32):
                pygame.draw.line(scr, (24, 29, 39), (gx, 0), (gx, h), 1)
            for gy in range(0, h, 32):
                pygame.draw.line(scr, (24, 29, 39), (0, gy), (w, gy), 1)

            # Tiêu đề chính có bóng chữ
            title_str = "TANK BATTLE  •  AI ARENA"
            scr.blit(self.font_title.render(title_str, True, (10, 12, 16)), (34, 22))
            scr.blit(self.font_title.render(title_str, True, (255, 210, 70)), (32, 20))
            scr.blit(self.font_sub.render("TDTU AI FINAL PROJECT — ZERO-SUM GAME SIMULATOR", True, (110, 180, 240)), (34, 56))

            # 3 Thẻ cấu hình
            self._draw_card(92, "Q", "Tank 1 (MAX Player)", self.label(self.options[self.sel[0]]), (46, 204, 113))
            self._draw_card(156, "W", "Tank 2 (MIN Player)", self.label(self.options[self.sel[1]]), (245, 130, 48))
            self._draw_card(220, "M", "Battlefield Map", self.maps[self.sel[2]], (85, 195, 255))

            # Thanh nút bấm dưới cùng
            btn_rect = pygame.Rect(32, 292, w - 64, 42)
            pygame.draw.rect(scr, (36, 135, 80), btn_rect, border_radius=8)
            pygame.draw.rect(scr, (90, 230, 145), btn_rect, 2, border_radius=8)
            cta = self.font.render("PRESS [ENTER] OR [SPACE] TO LAUNCH MATCH     •     [ESC] EXIT", True, (255, 255, 255))
            scr.blit(cta, (btn_rect.centerx - cta.get_width() // 2, btn_rect.centery - cta.get_height() // 2))

            pygame.display.flip()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return None
                    if ev.key == pygame.K_q:
                        self.sel[0] = (self.sel[0] + 1) % len(self.options)
                    if ev.key == pygame.K_w:
                        self.sel[1] = (self.sel[1] + 1) % len(self.options)
                    if ev.key == pygame.K_m:
                        self.sel[2] = (self.sel[2] + 1) % len(self.maps)
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return {
                            "a1": self.options[self.sel[0]],
                            "a2": self.options[self.sel[1]],
                            "map": os.path.join(self.base, "maps", self.maps[self.sel[2]]),
                        }
            clock.tick(30)


def load_agent_builtin(name):
    from CK_AI_26_27.Liem_B.task2_tank.plugin_loader import SafeAgent
    return SafeAgent(BUILTIN[name]())