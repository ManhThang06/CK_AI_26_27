import argparse
import os
import textwrap
from pathlib import Path

class KakuroApp:
    BG = (15, 23, 36)
    PANEL = (24, 36, 53)
    TEXT = (229, 237, 247)
    MUTED = (151, 168, 188)
    ACCENT = (71, 205, 184)
    COLORS = {"start": (183, 199, 221), "assign": (91, 168, 255),
              "propagate": (71, 205, 184), "contradiction": (255, 111, 117),
              "backtrack": (255, 186, 91), "solution": (131, 222, 137),
              "exhausted": (255, 111, 117), "limit": (255, 186, 91)}

    def __init__(self, trace_path):
        import pygame
        from .player import TracePlayer
        self.pg = pygame
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 830))
        pygame.display.set_caption("Kakuro | Domains and search trace")
        self.fonts = {s: pygame.font.SysFont("Segoe UI,Arial", s) for s in (13, 15, 17, 20, 24, 30, 38)}
        self.player = TracePlayer.load(trace_path)
        self.trace_path = Path(trace_path)
        self.selected = None
        self.buttons = []
        self.samples = Path(__file__).resolve().parents[1] / "traces"
        self.clock = pygame.time.Clock()

    def text(self, text, position, size=17, color=None):
        self.screen.blit(self.fonts[size].render(str(text), True, color or self.TEXT), position)

    def button(self, label, rect, action, active=False):
        pg = self.pg
        rect = pg.Rect(rect)
        pg.draw.rect(self.screen, (38, 78, 85) if active else (38, 52, 72), rect, border_radius=7)
        image = self.fonts[17].render(label, True, self.TEXT)
        self.screen.blit(image, image.get_rect(center=rect.center))
        self.buttons.append((rect, action))

    def load_sample(self, filename):
        from .player import TracePlayer
        self.trace_path = self.samples / filename
        self.player = TracePlayer.load(self.trace_path)
        self.selected = None

    def action(self, action):
        p = self.player
        if action == "next":
            p.playing = False
            p.next()
        elif action == "previous":
            p.previous()
        elif action == "toggle":
            p.toggle()
        elif action == "reset":
            p.reset()
        elif action == "slower":
            p.speed = max(.5, p.speed / 2)
        elif action == "faster":
            p.speed = min(32, p.speed * 2)
        elif action.startswith("sample:"):
            self.load_sample(action.split(":", 1)[1])

    def draw_board(self):
        pg, puzzle, event = self.pg, self.player.puzzle, self.player.current
        self.cell_size = min(108, 594 // max(puzzle.rows, puzzle.cols))
        self.origin = (32, 145)
        s = self.cell_size
        for r, row in enumerate(puzzle.grid):
            for c, token in enumerate(row):
                rect = pg.Rect(32 + c * s, 145 + r * s, s - 1, s - 1)
                if token != ".":
                    pg.draw.rect(self.screen, (49, 64, 84), rect)
                    if token != "#":
                        pg.draw.line(self.screen, (111, 133, 157), rect.topleft, rect.bottomright, 1)
                        for clue in token.split("/"):
                            image = self.fonts[17 if s < 80 else 20].render(clue[1:], True, self.TEXT)
                            pos = (rect.right - image.get_width() - 7, rect.top + 6) if clue[0] == "a" else (rect.left + 7, rect.bottom - image.get_height() - 6)
                            self.screen.blit(image, pos)
                    continue
                cell = f"{r},{c}"
                domain = event["domains"][cell]
                background = (239, 244, 249)
                if self.selected and cell in puzzle.peers[self.selected]:
                    background = (218, 231, 243)
                if event.get("cell") == cell:
                    color = self.COLORS[event["kind"]]
                    background = tuple(int(.5 * x + .5 * 255) for x in color)
                pg.draw.rect(self.screen, background, rect)
                if cell == self.selected:
                    pg.draw.rect(self.screen, (61, 113, 195), rect, 3)
                if len(domain) == 1:
                    image = self.fonts[38 if s >= 80 else 30].render(str(domain[0]), True, (24, 54, 76))
                    self.screen.blit(image, image.get_rect(center=rect.center))
                else:
                    for value in range(1, 10):
                        cx = rect.left + (value - 1) % 3 * s / 3 + s / 6
                        cy = rect.top + (value - 1) // 3 * s / 3 + s / 6
                        if value in domain:
                            image = self.fonts[15 if s < 80 else 20].render(str(value), True, (49, 78, 102))
                            self.screen.blit(image, image.get_rect(center=(cx, cy)))
                        elif cell == event.get("cell") and value in event.get("removed", []):
                            image = self.fonts[15 if s < 80 else 20].render(str(value), True, (195, 52, 68))
                            target = image.get_rect(center=(cx, cy))
                            self.screen.blit(image, target)
                            pg.draw.line(self.screen, (195, 52, 68), target.midleft, target.midright, 2)

    def draw(self):
        pg, p, event = self.pg, self.player, self.player.current
        self.screen.fill(self.BG)
        self.buttons = []
        self.text("KAKURO", (32, 22), 30)
        self.text("Inspect domains. Follow each deduction.", (32, 63), 17, self.MUTED)
        self.button("1   Example 5 x 5", (32, 100, 187, 32), "sample:assignment_5x5.json")
        self.button("2   Complex 9 x 9", (228, 100, 187, 32), "sample:assignment_9x9.json")
        self.button("3   Backtracking", (424, 100, 202, 32), "sample:backtrack_demo.json")
        self.draw_board()
        pg.draw.rect(self.screen, self.PANEL, (654, 24, 518, 718), border_radius=12)
        self.text("SEARCH TRACE", (678, 44), 20)
        self.text(p.puzzle.name, (678, 78), 17, self.MUTED)
        self.text(f"{p.index + 1:03d} / {len(p.events):03d}", (678, 119), 30)
        self.text(event["kind"].upper(), (883, 127), 20, self.COLORS[event["kind"]])
        labels = [("NODES", event.get("nodes", 0)), ("BACKTRACKS", event.get("backtracks", 0)),
                  ("DEPTH", event.get("depth", 0))]
        for i, (label, value) in enumerate(labels):
            self.text(label, (678 + 157 * i, 175), 13, self.MUTED)
            self.text(value, (678 + 157 * i, 196), 24)
        y = 248
        for line in textwrap.wrap(event.get("message", ""), width=48):
            self.text(line, (678, y), 17)
            y += 24
        cell = self.selected or event.get("cell")
        self.text("CELL INSPECTOR", (678, 340), 15, self.MUTED)
        if cell:
            self.text(f"({cell})  domain: {event['domains'][cell]}", (678, 367), 17)
            runs = [r for r in p.puzzle.runs if cell in r.cells]
            for i, run in enumerate(runs):
                self.text(f"{run.id}   sum {run.target}   {len(run.cells)} cells", (678, 399 + i * 25), 15, self.MUTED)
        else:
            self.text("Click a white cell to inspect its runs.", (678, 367), 17, self.MUTED)
        self.text("RECENT EVENTS", (678, 470), 15, self.MUTED)
        for j, i in enumerate(range(max(0, p.index - 5), p.index + 1)):
            e = p.events[i]
            self.text(f"{i+1:03d}  {e['kind']:14s} {e.get('cell') or '-'}", (678, 496 + 25 * j), 15,
                      self.COLORS[e["kind"]] if i == p.index else self.MUTED)
        self.text("Blue: guess   Teal: propagation", (678, 674), 15, self.MUTED)
        self.text("Amber: restore   Red strike: removed value", (678, 699), 15, self.MUTED)
        for label, x, width, action in [("Reset", 32, 90, "reset"), ("Back", 132, 90, "previous"),
                                        ("Pause" if p.playing else "Play", 232, 90, "toggle"),
                                        ("Next", 332, 90, "next"), ("-", 444, 42, "slower"),
                                        ("+", 570, 42, "faster")]:
            self.button(label, (x, 758, width, 37), action, action == "toggle" and p.playing)
        self.text(f"{p.speed:g}/s", (500, 768), 15)
        self.text("Space: play/pause   Arrows: step   R: reset   1/2/3: puzzle   +/-: speed", (32, 804), 13, self.MUTED)
        self.text("Snapshot replay / no solver running in UI thread", (678, 769), 15, self.MUTED)
        pg.display.flip()

    def handle(self, event):
        pg = self.pg
        if event.type == pg.QUIT:
            return False
        if event.type == pg.KEYDOWN:
            keys = {pg.K_SPACE: "toggle", pg.K_RIGHT: "next", pg.K_LEFT: "previous", pg.K_r: "reset",
                    pg.K_MINUS: "slower", pg.K_EQUALS: "faster", pg.K_PLUS: "faster",
                    pg.K_1: "sample:assignment_5x5.json", pg.K_2: "sample:assignment_9x9.json",
                    pg.K_3: "sample:backtrack_demo.json"}
            if event.key == pg.K_ESCAPE:
                return False
            if event.key in keys:
                self.action(keys[event.key])
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.buttons:
                if rect.collidepoint(event.pos):
                    self.action(action)
                    return True
            x, y = event.pos
            c, r = (x - 32) // self.cell_size, (y - 145) // self.cell_size
            cell = f"{r},{c}"
            self.selected = cell if cell in self.player.puzzle.cells else None
        return True

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000
            for event in self.pg.event.get():
                running = self.handle(event) and running
            self.player.tick(dt)
            self.draw()
        self.pg.quit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path,
                        default=Path(__file__).resolve().parents[1] / "traces" / "assignment_9x9.json")
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--event", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    app = KakuroApp(args.trace)
    app.player.index = args.event % len(app.player.events)
    if args.screenshot:
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        app.draw()
        app.pg.image.save(app.screen, str(args.screenshot))
        app.pg.quit()
    else:
        app.run()

if __name__ == "__main__":
    main()