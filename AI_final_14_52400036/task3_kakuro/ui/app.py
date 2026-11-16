"""Giao dien PyGame: hien thi mien cua tung o, qua trinh lan truyen rang buoc va Backtracking.

Moi puzzle trong thu muc puzzles/ deu duoc nap tu dong (cac nut 1..9 / phim Tab).
Logic doc du lieu (ngan xep phep doan, run dang loc, to hop con hop le, tong ket) nam o
ui/player.py; cac lop View trong ui/views.py chi ve; InputController doi su kien thanh hanh dong;
KakuroApp noi cac phan do voi nhau va quan ly phien solver.
"""
import argparse
import os
import sys
from pathlib import Path


class KakuroApp:
    WINDOW = (1200, 860)

    def __init__(self, puzzle_path=None, variable="mrv-degree", value="lcv"):
        import pygame
        from ..puzzle import PUZZLE_DIR, Puzzle, PuzzleRepository
        from .canvas import Canvas
        from .input import InputController
        from .theme import Theme
        from .views import (BoardView, ControlBarView, PuzzleTabsView, TimelineView,
                            TracePanelView)
        self.pg = pygame
        self.puzzles, self.load_errors = PuzzleRepository().load_all()
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
        self.canvas = Canvas(pygame, self.screen, Theme)
        self.tabs = PuzzleTabsView(self.canvas)
        self.board_view = BoardView(self.canvas)
        self.timeline = TimelineView(self.canvas)
        self.panel = TracePanelView(self.canvas)
        self.controls = ControlBarView(self.canvas)
        self.input = InputController(self)
        self.selected = None              # Cell dang duoc chon de xem
        self.session = None
        self.player = None
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

    # ------------------------------------------------------------ hanh dong
    def perform(self, action):
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
            self.perform(f"puzzle:{(self.puzzle_index + 1) % len(self.puzzles)}")
        elif action == "finish":
            self.session.finish()
        elif action.startswith(("var:", "val:")):
            # doi heuristic: chay lai solver tren puzzle hien tai
            key = "variable" if action.startswith("var:") else "value"
            self.config[key] = action.split(":", 1)[1]
            self.start_live(self.player.puzzle)
        elif action in ("cycle_var", "cycle_val"):
            from ..solver import SolverFactory
            key, names = (("variable", SolverFactory.variable_names()) if action == "cycle_var"
                          else ("value", SolverFactory.value_names()))
            nxt = names[(names.index(self.config[key]) + 1) % len(names)]
            self.perform(("var:" if key == "variable" else "val:") + nxt)

    # ------------------------------------------------------------ khung hinh
    def draw(self):
        self.canvas.begin_frame()
        self.tabs.draw(self.puzzles, self.puzzle_index)
        self.board_view.draw(self.player, self.selected)
        self.timeline.draw(self.player)
        self.panel.draw(self.player, self.selected, self.config)
        self.controls.draw(self.player)
        self.pg.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000
            for event in self.pg.event.get():
                running = self.input.handle(event) and running
            self.player.tick(dt)
            self.draw()
        self.close()

    def close(self):
        self.stop_session()
        self.pg.quit()

    def save_screenshot(self, path, event_index):
        """Chup anh khong cua so: cho solver chay het roi moi chon su kien."""
        self.session.finish()
        self.session.wait_finished()
        self.player.sync()
        self.player.index = event_index % len(self.player.events)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.draw()
        self.pg.image.save(self.screen, str(path))


class AppLauncher:
    """Doc tham so dong lenh roi khoi dong KakuroApp."""

    @staticmethod
    def build_parser():
        from ..solver import SolverFactory
        parser = argparse.ArgumentParser(description="Kakuro: solver chay song song voi UI")
        parser.add_argument("--puzzle", type=Path, help="file puzzle JSON (mac dinh: 9x9 trong puzzles/)")
        parser.add_argument("--variable", default="mrv-degree", choices=SolverFactory.variable_names())
        parser.add_argument("--value", default="lcv", choices=SolverFactory.value_names())
        parser.add_argument("--screenshot", type=Path)
        parser.add_argument("--event", type=int, default=0)
        parser.add_argument("--headless", action="store_true")
        return parser

    def launch(self, argv=None):
        args = self.build_parser().parse_args(argv)
        if args.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"
        app = KakuroApp(args.puzzle, args.variable, args.value)
        if args.screenshot:
            app.save_screenshot(args.screenshot, args.event)
            app.close()
        else:
            app.run()


if __name__ == "__main__":
    AppLauncher().launch()
