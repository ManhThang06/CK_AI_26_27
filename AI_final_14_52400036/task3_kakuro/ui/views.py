"""Cac View: moi lop ve mot vung cua man hinh tu du lieu cua LivePlayer (chi ve, khong co logic)."""
import textwrap
from abc import ABC, abstractmethod

from ..model.cell import Cell


class View(ABC):
    def __init__(self, canvas):
        self.canvas = canvas
        self.theme = canvas.theme

    @abstractmethod
    def draw(self, *args):
        """Ve vung cua view len canvas."""


class PuzzleTabsView(View):
    def draw(self, puzzles, current):
        c = self.canvas
        c.text("KAKURO", (32, 22), 30)
        c.text("Inspect domains. Follow each deduction.", (32, 63), 17, self.theme.MUTED)
        x = 32
        for i, puzzle in enumerate(puzzles):
            width = max(70, 30 + c.fonts[17].size(puzzle.label)[0])
            if x + width > 626:
                break
            flag = "!" if puzzle.warnings else ""
            c.button(f"{i + 1}  {puzzle.label}{flag}", (x, 100, width, 32), f"puzzle:{i}",
                     i == current)
            x += width + 8


class BoardView(View):
    ORIGIN = (32, 145)
    SIZE = 594

    def __init__(self, canvas):
        super().__init__(canvas)
        self.cell_size = 1

    def cell_at(self, pos, puzzle):
        """Cell trang duoi con tro chuot, hoac None."""
        x, y = pos
        cell = Cell((y - self.ORIGIN[1]) // self.cell_size, (x - self.ORIGIN[0]) // self.cell_size)
        return cell if puzzle.board.is_white(cell.row, cell.col) else None

    def draw(self, player, selected):
        c, t = self.canvas, self.theme
        pg = c.pg
        puzzle, event = player.puzzle, player.current
        s = self.cell_size = min(108, self.SIZE // max(puzzle.board.rows, puzzle.board.cols))
        x0, y0 = self.ORIGIN
        guesses = player.guess_cells(event)
        run = player.highlighted_run(event)
        run_cells = set(run.cells) if run else set()
        run_tint = t.blend(t.EVENT_COLORS[event["kind"]], (255, 255, 255), .72) if run else None
        clue_font = 20 if s >= 80 else 17 if s >= 60 else 13
        mark_font = clue_font
        selected_runs = ({x for r in puzzle.runs if selected in r.cells for x in r.cells}
                         if selected else set())
        for r in range(puzzle.board.rows):
            for col in range(puzzle.board.cols):
                rect = pg.Rect(x0 + col * s, y0 + r * s, s - 1, s - 1)
                if not puzzle.board.is_white(r, col):
                    self._draw_clue_square(rect, puzzle.board.clue_at(r, col), clue_font)
                    continue
                cell = Cell(r, col)
                self._draw_white_square(rect, cell, event, guesses, selected, selected_runs,
                                        run_cells, run_tint, mark_font)

    def _draw_clue_square(self, rect, clue, font):
        c, pg = self.canvas, self.canvas.pg
        pg.draw.rect(c.screen, (49, 64, 84), rect)
        if clue is None:
            return
        pg.draw.line(c.screen, (111, 133, 157), rect.topleft, rect.bottomright, 1)
        if clue.across is not None:
            image = c.fonts[font].render(str(clue.across), True, self.theme.TEXT)
            c.screen.blit(image, (rect.right - image.get_width() - 4, rect.top + 3))
        if clue.down is not None:
            image = c.fonts[font].render(str(clue.down), True, self.theme.TEXT)
            c.screen.blit(image, (rect.left + 4, rect.bottom - image.get_height() - 3))

    def _draw_white_square(self, rect, cell, event, guesses, selected, selected_runs,
                           run_cells, run_tint, mark_font):
        c, t = self.canvas, self.theme
        pg, s = c.pg, self.cell_size
        key = cell.key
        domain = event["domains"][key]
        background = (239, 244, 249)
        if cell in selected_runs:
            background = (218, 231, 243)
        if cell in run_cells:                       # run dang duoc loc / gay mau thuan
            background = run_tint
        if event.get("cell") == key:
            background = t.blend(t.EVENT_COLORS[event["kind"]], (255, 255, 255), .5)
        pg.draw.rect(c.screen, background, rect)
        if key in guesses:                          # o la phep doan: vien xanh
            pg.draw.rect(c.screen, t.GUESS_INK, rect, 3)
        if cell == selected:
            pg.draw.rect(c.screen, (140, 90, 200), rect, 3 if key not in guesses else 1)
        if len(domain) == 1:
            ink = t.GUESS_INK if key in guesses else t.DEDUCED_INK
            image = c.fonts[38 if s >= 80 else 30 if s >= 60 else 24].render(str(domain[0]), True, ink)
            c.screen.blit(image, image.get_rect(center=rect.center))
            return
        for value in range(1, 10):
            cx = rect.left + (value - 1) % 3 * s / 3 + s / 6
            cy = rect.top + (value - 1) // 3 * s / 3 + s / 6
            if value in domain:
                image = c.fonts[mark_font].render(str(value), True, (30, 52, 72))
                c.screen.blit(image, image.get_rect(center=(cx, cy)))
            elif key == event.get("cell") and value in event.get("removed", []):
                image = c.fonts[mark_font].render(str(value), True, (195, 52, 68))
                target = image.get_rect(center=(cx, cy))
                c.screen.blit(image, target)
                pg.draw.line(c.screen, (195, 52, 68), target.midleft, target.midright, 2)


class TimelineView(View):
    RECT = (32, 748, 594, 16)     # x, y, rong, cao

    def contains(self, pos):
        x, y, w, h = self.RECT
        return x <= pos[0] < x + w and y - 4 <= pos[1] < y + h + 4

    def fraction(self, x):
        tx, _, tw, _ = self.RECT
        return min(1.0, max(0.0, (x - tx) / (tw - 1)))

    def draw(self, player):
        """Moi cot la loai su kien noi bat nhat; bam / keo de nhay toi do."""
        c, t = self.canvas, self.theme
        x, y, w, h = self.RECT
        c.pg.draw.rect(c.screen, t.PANEL, (x, y, w, h), border_radius=4)
        faint = t.blend(t.EVENT_COLORS["propagate"], t.PANEL, .65)
        for i, kind in enumerate(player.timeline(w)):
            if kind is None:
                continue
            color = faint if kind in ("propagate", "start") else t.EVENT_COLORS[kind]
            c.pg.draw.line(c.screen, color, (x + i, y + 2), (x + i, y + h - 3))
        px = x + int(player.progress * (w - 1))
        c.pg.draw.rect(c.screen, t.TEXT, (px - 1, y - 2, 3, h + 4))


class ControlBarView(View):
    def draw(self, player):
        c = self.canvas
        for label, bx, width, action in [("Reset", 32, 76, "reset"), ("Back", 116, 76, "previous"),
                                         ("Pause" if player.playing else "Play", 200, 76, "toggle"),
                                         ("Next", 284, 76, "next"), ("-", 376, 36, "slower"),
                                         ("+", 480, 36, "faster")]:
            c.button(label, (bx, 778, width, 37), action, action == "toggle" and player.playing)
        c.text(f"{player.speed:g}/s", (424, 788), 15)
        for label, bx, width, action in [("Next guess", 678, 112, "next_guess"),
                                         ("Next backtrack", 798, 140, "next_backtrack"),
                                         ("Finish", 946, 90, "finish")]:
            c.button(label, (bx, 778, width, 37), action,
                     action == "next_guess" and bool(player.seek_kinds))
        c.text("Space play/pause   Arrows step   G next guess   B next backtrack   R reset   "
               "1-9 / Tab puzzle   F finish   V/C heuristic   +/- speed   click cell or timeline",
               (32, 830), 13, self.theme.MUTED)


class TracePanelView(View):
    LEFT, RIGHT = 678, 1148

    def draw(self, player, selected, config):
        c, t = self.canvas, self.theme
        event, left, right = player.current, self.LEFT, self.RIGHT
        c.pg.draw.rect(c.screen, t.PANEL, (654, 24, 518, 744), border_radius=12)
        c.text("SEARCH TRACE", (left, 44), 20)
        c.text(player.status_text, (right, 48), 15, t.MUTED, right=True)
        c.text(f"{player.puzzle.name}   [{player.config['variable']} + {player.config['value']}]",
               (left, 78), 17, t.MUTED)
        if player.puzzle.warnings:
            c.text("WARNING: " + player.puzzle.warnings[-1][:62], (left, 100), 13,
                   t.EVENT_COLORS["backtrack"])
        c.text(f"{player.index + 1:03d} / {player.total_text}", (left, 119), 30)
        c.text(event["kind"].upper(), (883, 127), 20, t.EVENT_COLORS[event["kind"]])
        for i, (label, value) in enumerate([("NODES", event.get("nodes", 0)),
                                            ("BACKTRACKS", event.get("backtracks", 0)),
                                            ("DEPTH", event.get("depth", 0))]):
            c.text(label, (left + 157 * i, 175), 13, t.MUTED)
            c.text(value, (left + 157 * i, 196), 24)
        y = 240
        for line in textwrap.wrap(event.get("message", ""), width=48)[:3]:
            c.text(line, (left, y), 17)
            y += 24
        self._draw_guess_stack(event)
        self._draw_inspector(player, event, selected)
        self._draw_bottom(player, config)

    def _draw_guess_stack(self, event):
        """Ngan xep cac phep doan dang mo; o backtrack thi bao phep vua bi hoan tac."""
        c, t = self.canvas, self.theme
        left, right = self.LEFT, self.RIGHT
        guesses = event["guesses"]
        shown = guesses[-10:]
        head = f"GUESS STACK (depth {len(guesses)}"
        head += f", last {len(shown)} shown)" if len(guesses) > len(shown) else ")"
        c.text(head, (left, 322), 15, t.MUTED)
        if event["kind"] == "backtrack":
            c.text(f"undone ({event['cell']})={event['value']}", (right, 322), 15,
                   t.EVENT_COLORS["backtrack"], right=True)
        if not guesses:
            c.text("no guesses yet (propagation only)", (left, 348), 15, t.MUTED)
            return
        x, y = left, 344
        for i, (cell, value) in enumerate(shown):
            label = f"({cell})={value}"
            width = c.fonts[15].size(label)[0] + 14
            if x + width > right:
                x, y = left, y + 28
                if y > 372:
                    break
            last = i == len(shown) - 1
            c.pg.draw.rect(c.screen,
                           t.blend(t.EVENT_COLORS["assign"], t.PANEL, .55 if last else .8),
                           (x, y, width, 24), border_radius=6)
            c.text(label, (x + 7, y + 2), 15, t.TEXT if last else t.MUTED)
            x += width + 6

    def _draw_inspector(self, player, event, selected):
        """O dang chon (hoac o cua su kien): mien, va tung run chua o do voi cac to hop con hop le."""
        c, t, left = self.canvas, self.theme, self.LEFT
        cell = selected or (Cell.parse(event["cell"]) if event.get("cell") else None)
        c.text("CELL INSPECTOR", (left, 408), 15, t.MUTED)
        if cell is None:
            c.text("Click a white cell to inspect its runs.", (left, 432), 17, t.MUTED)
            return
        c.text(f"({cell.key})  domain: {event['domains'][cell.key]}", (left, 430), 17)
        y = 458
        for run in [r for r in player.puzzle.runs if cell in r.cells][:2]:
            d = player.run_details(run, event)
            used = ",".join(map(str, d["used"])) or "-"
            c.text(f"{d['id']}  sum {d['target']}, {d['size']} cells, fixed {used}, "
                   f"need {d['rest']} from {d['free']} free", (left, y), 15,
                   t.EVENT_COLORS["propagate"] if run.name == event.get("run") else t.MUTED)
            combos = ["".join(map(str, combo)) for combo in d["combos"]]
            c.text("sets: " + (c.fit(combos, 410) if combos else "none (dead end)"),
                   (left + 14, y + 20), 15, t.TEXT)
            y += 46

    def _draw_bottom(self, player, config):
        c, t, left = self.canvas, self.theme, self.LEFT
        summary = player.summary()
        if summary:
            self._draw_summary(player, summary)
        else:
            c.text("RECENT EVENTS", (left, 556), 15, t.MUTED)
            for j, i in enumerate(range(max(0, player.index - 3), player.index + 1)):
                e = player.events[i]
                detail = {"propagate": f"del {','.join(map(str, e.get('removed', [])))}",
                          "assign": f"= {e.get('value', '')}",
                          "backtrack": f"undo = {e.get('value', '')}"}.get(e["kind"], "")
                c.text(f"{i + 1:03d}  {e['kind']:13s} {(e.get('cell') or '-'):6s} {detail}",
                       (left, 578 + 22 * j), 15,
                       t.EVENT_COLORS[e["kind"]] if i == player.index else t.MUTED)
        self._draw_heuristic_buttons(config)
        x = left
        for label, key in (("Guess", "assign"), ("Propagation", "propagate"), ("Undo", "backtrack"),
                           ("Dead end", "contradiction"), ("Solution", "solution")):
            c.pg.draw.rect(c.screen, t.EVENT_COLORS[key], (x, 752, 11, 11), border_radius=3)
            x += 16 + c.text(label, (x + 16, 748), 13, t.MUTED) + 12

    def _draw_heuristic_buttons(self, config):
        c, left = self.canvas, self.LEFT
        c.text("Variable", (left, 689), 15, self.theme.MUTED)
        for name, x, width in (("first", 760, 70), ("mrv", 836, 70), ("mrv-degree", 912, 120)):
            c.button(name, (x, 682, width, 28), "var:" + name, config["variable"] == name)
        c.text("Value", (left, 723), 15, self.theme.MUTED)
        for name, x, width in (("asc", 760, 70), ("lcv", 836, 70)):
            c.button(name, (x, 716, width, 28), "val:" + name, config["value"] == name)

    def _draw_summary(self, player, s):
        c, t, left = self.canvas, self.theme, self.LEFT
        ok = s["kind"] == "solution"
        title = ("SOLVED, verified by Puzzle.check" if ok
                 else "NO SOLUTION" if s["kind"] == "exhausted" else "STOPPED AT NODE LIMIT")
        c.text("RESULT", (left, 556), 15, t.MUTED)
        c.text(title, (left, 578), 20, t.EVENT_COLORS["solution" if ok else s["kind"]])
        c.text(f"nodes {s['nodes']}   backtracks {s['backtracks']}   max depth {s['max_depth']}",
               (left, 608), 15)
        c.text(f"{s['events']} trace events   solver alone: {s['ms']:.2f} ms", (left, 631), 15,
               t.MUTED)
        if s["kind"] == "exhausted" and player.puzzle.warnings:
            c.text("see warning above: the puzzle itself is inconsistent", (left, 654), 13,
                   t.EVENT_COLORS["backtrack"])
