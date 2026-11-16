"""Canvas: boc man hinh pygame (ve chu, nut bam) cho cac View; khong biet gi ve Kakuro."""


class Button:
    def __init__(self, rect, label, action, active=False):
        self.rect = rect
        self.label = label
        self.action = action
        self.active = active

    def hit(self, pos):
        return self.rect.collidepoint(pos)


class Canvas:
    def __init__(self, pygame, screen, theme):
        self.pg = pygame
        self.screen = screen
        self.theme = theme
        self.fonts = {s: pygame.font.SysFont("Segoe UI,Arial", s) for s in theme.FONT_SIZES}
        self.buttons = []

    def begin_frame(self):
        self.screen.fill(self.theme.BG)
        self.buttons = []

    def text(self, text, position, size=17, color=None, right=False):
        image = self.fonts[size].render(str(text), True, color or self.theme.TEXT)
        x, y = position
        self.screen.blit(image, (x - image.get_width() if right else x, y))
        return image.get_width()

    def fit(self, items, max_width, size=15):
        """Noi cac chuoi bang dau cach cho vua `max_width`; phan thua thay bang '... (+n)'."""
        out, width = [], 0
        for i, item in enumerate(items):
            w = self.fonts[size].size(item + " ")[0]
            if width + w > max_width:
                out.append(f"... (+{len(items) - i})")
                break
            out.append(item)
            width += w
        return " ".join(out)

    def button(self, label, rect, action, active=False):
        button = Button(self.pg.Rect(rect), label, action, active)
        self.pg.draw.rect(self.screen, (38, 78, 85) if active else (38, 52, 72), button.rect,
                          border_radius=7)
        image = self.fonts[17].render(label, True, self.theme.TEXT)
        self.screen.blit(image, image.get_rect(center=button.rect.center))
        self.buttons.append(button)

    def button_at(self, pos):
        return next((b for b in self.buttons if b.hit(pos)), None)
