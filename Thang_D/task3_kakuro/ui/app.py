"""Giao dien PyGame: hien thi mien cua tung o, qua trinh lan truyen rang buoc va Backtracking.

Moi puzzle trong thu muc puzzles/ deu duoc nap tu dong (cac nut 1..9 / phim Tab).
Toan bo logic doc du lieu (ngan xep phep doan, run dang loc, to hop con hop le, tong ket)
nam trong ui/player.py; file nay chi ve.
"""
import argparse
import os
import sys
import textwrap
from pathlib import Path


def blend(color, other=(255, 255, 255), ratio=.5):
    return tuple(int(ratio * o + (1 - ratio) * c) for c, o in zip(color, other))


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
    GUESS_INK = (26, 92, 200)         # chu so cua o dang la phep doan
    DEDUCED_INK = (16, 104, 92)       # chu so do lan truyen suy ra
    BOARD_X, BOARD_Y, BOARD_SIZE = 32, 145, 594
    TIMELINE = (32, 748, 594, 16)     # x, y, rong, cao
    WINDOW = (1200, 860)

    def __init__(self, puzzle_path=None, variable="mrv-degree", value="lcv"):
        import pygame
        from ..puzzle import PUZZLE_DIR, Puzzle, load_all
        self.pg = pygame
        self.puzzles, self.load_errors = load_all()
        for path, message in self.load_errors:
            print(f"[skip] {Path(path).name}: {message}", file=sys.stderr)
        start = None
        if puzzle_path:
            requested = Puzzle.load(puzzle_path)
            same = [i for i, p in enumerate(self.puzzles)
                    if p.path and requested.path and p.path.resolve() == requested.path.resolve()]
            if same:
                start = same[0]
            else:
                self.puzzles.insert(0, requested)
                start = 0
        if not self.puzzles:
            raise SystemExit(f"Khong tim thay puzzle hop le nao trong {PUZZLE_DIR}")
        if start is None:
            start = next((i for i, p in enumerate(self.puzzles) if p.label == "9x9"), 0)
        pygame.init()
        self.screen = pygame.display.set_mode(self.WINDOW)
        pygame.display.set_caption("Kakuro | Domains and search")
        self.fonts = {s: pygame.font.SysFont("Segoe UI,Arial", s) for s in (13, 15, 17, 20, 24, 30, 38)}
        self.selected = None
        self.buttons = []
        self.session = None
        self.dragging = False
        self.cell_size = 1
        self.puzzle_index = start
        self.config = {"variable": variable, "value": value}
        self.clock = pygame.time.Clock()
        self.start_live(self.puzzles[start])

    # ------------------------------------------------------------ phien solver
    def stop_session(self):
        if self.session:
            self.session.stop()
            self.session = None

    def start_live(self, puzzle):
        """Tao LiveSession moi (thread solver) voi cau hinh hien tai, thay cho phien cu."""
        from ..solver import LiveSession
        from .player import LivePlayer
        self.stop_session()
        session = LiveSession(puzzle, self.config["variable"], self.config["value"])
        session.start()
        self.session = session
        self.player = LivePlayer(session)
        self.selected = None

    # ------------------------------------------------------------ ve co ban
    def text(self, text, position, size=17, color=None, right=False):
        image = self.fonts[size].render(str(text), True, color or self.TEXT)
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
        pg = self.pg
        rect = pg.Rect(rect)
        pg.draw.rect(self.screen, (38, 78, 85) if active else (38, 52, 72), rect, border_radius=7)
        image = self.fonts[17].render(label, True, self.TEXT)
        self.screen.blit(image, image.get_rect(center=rect.center))
        self.buttons.append((rect, action))

    # ------------------------------------------------------------ hanh dong
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
        elif action == "next_guess":
            p.seek({"assign"})
        elif action == "next_backtrack":
            p.seek({"backtrack"})
        elif action == "slower":
            p.speed = max(.5, p.speed / 2)
        elif action == "faster":
            p.speed = min(32, p.speed * 2)
        elif action.startswith("puzzle:"):
            index = int(action.split(":", 1)[1])
            if 0 <= index < len(self.puzzles):
                self.puzzle_index = index
                self.start_live(self.puzzles[index])
        elif action == "next_puzzle":
            self.action(f"puzzle:{(self.puzzle_index + 1) % len(self.puzzles)}")
        elif action == "finish":
            self.session.finish()
        elif action.startswith(("var:", "val:")):
            # doi heuristic: chay lai solver tren puzzle hien tai
            key = "variable" if action.startswith("var:") else "value"
            self.config[key] = action.split(":", 1)[1]
            self.start_live(self.player.puzzle)
        elif action in ("cycle_var", "cycle_val"):
            from ..solver import VARIABLE_SELECTORS, VALUE_ORDERERS
            key, names = (("variable", list(VARIABLE_SELECTORS)) if action == "cycle_var"
                          else ("value", list(VALUE_ORDERERS)))
            nxt = names[(names.index(self.config[key]) + 1) % len(names)]
            self.action(("var:" if key == "variable" else "val:") + nxt)

    # ------------------------------------------------------------ ban co
    def draw_board(self):
        pg, p = self.pg, self.player
        puzzle, event = p.puzzle, p.current
        s = self.cell_size = min(108, self.BOARD_SIZE // max(puzzle.rows, puzzle.cols))
        x0, y0 = self.BOARD_X, self.BOARD_Y
        guesses = p.guess_cells(event)
        run = p.highlighted_run(event)
        run_cells = set(run.cells) if run else set()
        run_tint = blend(self.COLORS[event["kind"]], (255, 255, 255), .72) if run else None
        clue_font = 20 if s >= 80 else 17 if s >= 60 else 13
        mark_font = 20 if s >= 80 else 17 if s >= 60 else 13
        selected_runs = ({c for r in puzzle.runs if self.selected in r.cells for c in r.cells}
                         if self.selected else set())
        for r, row in enumerate(puzzle.grid):
            for c, token in enumerate(row):
                rect = pg.Rect(x0 + c * s, y0 + r * s, s - 1, s - 1)
                if token != ".":
                    pg.draw.rect(self.screen, (49, 64, 84), rect)
                    if token != "#":
                        pg.draw.line(self.screen, (111, 133, 157), rect.topleft, rect.bottomright, 1)
                        for clue in token.split("/"):
                            image = self.fonts[clue_font].render(clue[1:], True, self.TEXT)
                            pos = ((rect.right - image.get_width() - 4, rect.top + 3) if clue[0] == "a"
                                   else (rect.left + 4, rect.bottom - image.get_height() - 3))
                            self.screen.blit(image, pos)
                    continue
                cell = f"{r},{c}"
                domain = event["domains"][cell]
                background = (239, 244, 249)
                if cell in selected_runs:
                    background = (218, 231, 243)
                if cell in run_cells:                       # run dang duoc loc / gay mau thuan
                    background = run_tint
                if event.get("cell") == cell:
                    background = blend(self.COLORS[event["kind"]], (255, 255, 255), .5)
                pg.draw.rect(self.screen, background, rect)
                if cell in guesses:                         # o la phep doan: vien xanh
                    pg.draw.rect(self.screen, self.GUESS_INK, rect, 3)
                if cell == self.selected:
                    pg.draw.rect(self.screen, (140, 90, 200), rect, 3 if cell not in guesses else 1)
                if len(domain) == 1:
                    ink = self.GUESS_INK if cell in guesses else self.DEDUCED_INK
                    image = self.fonts[38 if s >= 80 else 30 if s >= 60 else 24].render(
                        str(domain[0]), True, ink)
                    self.screen.blit(image, image.get_rect(center=rect.center))
                else:
                    for value in range(1, 10):
                        cx = rect.left + (value - 1) % 3 * s / 3 + s / 6
                        cy = rect.top + (value - 1) // 3 * s / 3 + s / 6
                        if value in domain:
                            image = self.fonts[mark_font].render(str(value), True, (30, 52, 72))
                            self.screen.blit(image, image.get_rect(center=(cx, cy)))
                        elif cell == event.get("cell") and value in event.get("removed", []):
                            image = self.fonts[mark_font].render(str(value), True, (195, 52, 68))
                            target = image.get_rect(center=(cx, cy))
                            self.screen.blit(image, target)
                            pg.draw.line(self.screen, (195, 52, 68), target.midleft, target.midright, 2)

    def draw_timeline(self):
        """Thanh tien do: moi cot la loai su kien noi bat nhat; bam / keo de nhay toi do."""
        pg, p = self.pg, self.player
        x, y, w, h = self.TIMELINE
        pg.draw.rect(self.screen, self.PANEL, (x, y, w, h), border_radius=4)
        faint = blend(self.COLORS["propagate"], self.PANEL, .65)
        for i, kind in enumerate(p.timeline(w)):
            if kind is None:
                continue
            color = faint if kind in ("propagate", "start") else self.COLORS[kind]
            pg.draw.line(self.screen, color, (x + i, y + 2), (x + i, y + h - 3))
        px = x + int(p.progress * (w - 1))
        pg.draw.rect(self.screen, self.TEXT, (px - 1, y - 2, 3, h + 4))

    # ------------------------------------------------------------ bang ben phai
    def draw_panel(self):
        pg, p, event = self.pg, self.player, self.player.current
        left, right = 678, 1148
        pg.draw.rect(self.screen, self.PANEL, (654, 24, 518, 744), border_radius=12)
        self.text("SEARCH TRACE", (left, 44), 20)
        self.text(p.status_text, (right, 48), 15, self.MUTED, right=True)
        self.text(f"{p.puzzle.name}   [{p.meta['variable']} + {p.meta['value']}]", (left, 78), 17, self.MUTED)
        if p.puzzle.warnings:
            self.text("WARNING: " + p.puzzle.warnings[-1][:62], (left, 100), 13, self.COLORS["backtrack"])
        self.text(f"{p.index + 1:03d} / {p.total_text}", (left, 119), 30)
        self.text(event["kind"].upper(), (883, 127), 20, self.COLORS[event["kind"]])
        for i, (label, value) in enumerate([("NODES", event.get("nodes", 0)),
                                            ("BACKTRACKS", event.get("backtracks", 0)),
                                            ("DEPTH", event.get("depth", 0))]):
            self.text(label, (left + 157 * i, 175), 13, self.MUTED)
            self.text(value, (left + 157 * i, 196), 24)
        y = 240
        for line in textwrap.wrap(event.get("message", ""), width=48)[:3]:
            self.text(line, (left, y), 17)
            y += 24
        self.draw_guess_stack(event, left, right)
        self.draw_inspector(event, left)
        self.draw_bottom_panel(event, left)

    def draw_guess_stack(self, event, left, right):
        """Ngan xep cac phep doan dang mo; o backtrack thi bao phep vua bi hoan tac."""
        pg = self.pg
        guesses = event["guesses"]
        head = f"GUESS STACK (depth {len(guesses)}"
        shown = guesses[-10:]
        head += f", last {len(shown)} shown)" if len(guesses) > len(shown) else ")"
        self.text(head, (left, 322), 15, self.MUTED)
        if event["kind"] == "backtrack":
            self.text(f"undone ({event['cell']})={event['value']}", (right, 322), 15,
                      self.COLORS["backtrack"], right=True)
        if not guesses:
            self.text("no guesses yet (propagation only)", (left, 348), 15, self.MUTED)
            return
        x, y = left, 344
        for i, (cell, value) in enumerate(shown):
            label = f"({cell})={value}"
            width = self.fonts[15].size(label)[0] + 14
            if x + width > right:
                x, y = left, y + 28
                if y > 372:
                    break
            last = i == len(shown) - 1
            rect = pg.Rect(x, y, width, 24)
            pg.draw.rect(self.screen, blend(self.COLORS["assign"], self.PANEL, .55 if last else .8),
                         rect, border_radius=6)
            self.text(label, (x + 7, y + 2), 15, self.TEXT if last else self.MUTED)
            x += width + 6

    def draw_inspector(self, event, left):
        """O dang chon (hoac o cua su kien): mien, va tung run chua o do voi cac to hop con hop le."""
        p = self.player
        cell = self.selected or event.get("cell")
        self.text("CELL INSPECTOR", (left, 408), 15, self.MUTED)
        if not cell:
            self.text("Click a white cell to inspect its runs.", (left, 432), 17, self.MUTED)
            return
        self.text(f"({cell})  domain: {event['domains'][cell]}", (left, 430), 17)
        y = 458
        for run in [r for r in p.puzzle.runs if cell in r.cells][:2]:
            d = p.run_details(run, event)
            used = ",".join(map(str, d["used"])) or "-"
            self.text(f"{d['id']}  sum {d['target']}, {d['size']} cells, fixed {used}, "
                      f"need {d['rest']} from {d['free']} free", (left, y), 15,
                      self.COLORS["propagate"] if run.id == event.get("run") else self.MUTED)
            combos = ["".join(map(str, c)) for c in d["combos"]]
            self.text("sets: " + (self.fit(combos, 410) if combos else "none (dead end)"),
                      (left + 14, y + 20), 15, self.TEXT)
            y += 46

    def draw_bottom_panel(self, event, left):
        p = self.player
        summary = p.summary()
        if summary:
            self.draw_summary(summary, left)
        else:
            self.text("RECENT EVENTS", (left, 556), 15, self.MUTED)
            for j, i in enumerate(range(max(0, p.index - 3), p.index + 1)):
                e = p.events[i]
                detail = {"propagate": f"del {','.join(map(str, e.get('removed', [])))}",
                          "assign": f"= {e.get('value', '')}",
                          "backtrack": f"undo = {e.get('value', '')}"}.get(e["kind"], "")
                self.text(f"{i + 1:03d}  {e['kind']:13s} {(e.get('cell') or '-'):6s} {detail}",
                          (left, 578 + 22 * j), 15,
                          self.COLORS[e["kind"]] if i == p.index else self.MUTED)
        self.text("Variable", (left, 689), 15, self.MUTED)
        for name, x, width in (("first", 760, 70), ("mrv", 836, 70), ("mrv-degree", 912, 120)):
            self.button(name, (x, 682, width, 28), "var:" + name, self.config["variable"] == name)
        self.text("Value", (left, 723), 15, self.MUTED)
        for name, x, width in (("asc", 760, 70), ("lcv", 836, 70)):
            self.button(name, (x, 716, width, 28), "val:" + name, self.config["value"] == name)
        # chu giai mau
        x = left
        for label, key in (("Guess", "assign"), ("Propagation", "propagate"), ("Undo", "backtrack"),
                           ("Dead end", "contradiction"), ("Solution", "solution")):
            self.pg.draw.rect(self.screen, self.COLORS[key], (x, 752, 11, 11), border_radius=3)
            x += 16 + self.text(label, (x + 16, 748), 13, self.MUTED) + 12

    def draw_summary(self, s, left):
        ok = s["kind"] == "solution"
        title = ("SOLVED, verified by Puzzle.check" if ok
                 else "NO SOLUTION" if s["kind"] == "exhausted" else "STOPPED AT NODE LIMIT")
        self.text("RESULT", (left, 556), 15, self.MUTED)
        self.text(title, (left, 578), 20, self.COLORS["solution" if ok else s["kind"]])
        self.text(f"nodes {s['nodes']}   backtracks {s['backtracks']}   max depth {s['max_depth']}",
                  (left, 608), 15)
        self.text(f"{s['events']} trace events   solver alone: {s['ms']:.2f} ms", (left, 631), 15,
                  self.MUTED)
        if s["kind"] == "exhausted" and self.player.puzzle.warnings:
            self.text("see warning above: the puzzle itself is inconsistent", (left, 654), 13,
                      self.COLORS["backtrack"])

    # ------------------------------------------------------------ khung hinh
    def draw(self):
        pg, p = self.pg, self.player
        self.screen.fill(self.BG)
        self.buttons = []
        self.text("KAKURO", (32, 22), 30)
        self.text("Inspect domains. Follow each deduction.", (32, 63), 17, self.MUTED)
        x = 32
        for i, puzzle in enumerate(self.puzzles):
            width = max(70, 30 + self.fonts[17].size(puzzle.label)[0])
            if x + width > 626:
                break
            flag = "!" if puzzle.warnings else ""
            self.button(f"{i + 1}  {puzzle.label}{flag}", (x, 100, width, 32), f"puzzle:{i}",
                        i == self.puzzle_index)
            x += width + 8
        self.draw_board()
        self.draw_timeline()
        self.draw_panel()
        for label, bx, width, action in [("Reset", 32, 76, "reset"), ("Back", 116, 76, "previous"),
                                         ("Pause" if p.playing else "Play", 200, 76, "toggle"),
                                         ("Next", 284, 76, "next"), ("-", 376, 36, "slower"),
                                         ("+", 480, 36, "faster")]:
            self.button(label, (bx, 778, width, 37), action, action == "toggle" and p.playing)
        self.text(f"{p.speed:g}/s", (424, 788), 15)
        for label, bx, width, action in [("Next guess", 678, 112, "next_guess"),
                                         ("Next backtrack", 798, 140, "next_backtrack"),
                                         ("Finish", 946, 90, "finish")]:
            self.button(label, (bx, 778, width, 37), action, action == "next_guess" and bool(p.seek_kinds))
        self.text("Space play/pause   Arrows step   G next guess   B next backtrack   R reset   "
                  "1-9 / Tab puzzle   F finish   V/C heuristic   +/- speed   click cell or timeline",
                  (32, 830), 13, self.MUTED)
        pg.display.flip()

    # ------------------------------------------------------------ su kien
    def timeline_jump(self, x):
        tx, _, tw, _ = self.TIMELINE
        self.player.jump_fraction(min(1.0, max(0.0, (x - tx) / (tw - 1))))

    def in_timeline(self, pos):
        tx, ty, tw, th = self.TIMELINE
        return tx <= pos[0] < tx + tw and ty - 4 <= pos[1] < ty + th + 4

    def handle(self, event):
        pg = self.pg
        if event.type == pg.QUIT:
            return False
        if event.type == pg.KEYDOWN:
            keys = {pg.K_SPACE: "toggle", pg.K_RIGHT: "next", pg.K_LEFT: "previous", pg.K_r: "reset",
                    pg.K_MINUS: "slower", pg.K_EQUALS: "faster", pg.K_PLUS: "faster",
                    pg.K_f: "finish", pg.K_g: "next_guess", pg.K_b: "next_backtrack",
                    pg.K_TAB: "next_puzzle", pg.K_v: "cycle_var", pg.K_c: "cycle_val"}
            for i in range(min(9, len(self.puzzles))):
                keys[pg.K_1 + i] = f"puzzle:{i}"
            if event.key == pg.K_ESCAPE:
                return False
            if event.key in keys:
                self.action(keys[event.key])
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.buttons:
                if rect.collidepoint(event.pos):
                    self.action(action)
                    return True
            if self.in_timeline(event.pos):
                self.dragging = True
                self.timeline_jump(event.pos[0])
                return True
            x, y = event.pos
            c, r = (x - self.BOARD_X) // self.cell_size, (y - self.BOARD_Y) // self.cell_size
            cell = f"{r},{c}"
            self.selected = cell if cell in self.player.puzzle.cells else None
        if event.type == pg.MOUSEMOTION and self.dragging:
            self.timeline_jump(event.pos[0])
        if event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        return True

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000
            for event in self.pg.event.get():
                running = self.handle(event) and running
            self.player.tick(dt)
            self.draw()
        self.stop_session()
        self.pg.quit()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kakuro: solver chay song song voi UI")
    parser.add_argument("--puzzle", type=Path, help="file puzzle JSON (mac dinh: 9x9 trong puzzles/)")
    parser.add_argument("--variable", default="mrv-degree", choices=["first", "mrv", "mrv-degree"])
    parser.add_argument("--value", default="lcv", choices=["asc", "lcv"])
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--event", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args(argv)
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    app = KakuroApp(args.puzzle, args.variable, args.value)
    if args.screenshot:
        app.session.finish()              # chup anh: cho solver chay het roi moi chon su kien
        app.session.wait_finished()
        app.player.sync()
        app.player.index = args.event % len(app.player.events)
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        app.draw()
        app.pg.image.save(app.screen, str(args.screenshot))
        app.stop_session()
        app.pg.quit()
    else:
        app.run()


if __name__ == "__main__":
    main()
