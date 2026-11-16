"""InputController: doi su kien ban phim / chuot cua pygame thanh hanh dong cua KakuroApp."""


class InputController:
    def __init__(self, app):
        self.app = app
        self.pg = app.pg
        self.dragging = False

    def key_actions(self):
        pg = self.pg
        keys = {pg.K_SPACE: "toggle", pg.K_RIGHT: "next", pg.K_LEFT: "previous", pg.K_r: "reset",
                pg.K_MINUS: "slower", pg.K_EQUALS: "faster", pg.K_PLUS: "faster",
                pg.K_f: "finish", pg.K_g: "next_guess", pg.K_b: "next_backtrack",
                pg.K_TAB: "next_puzzle", pg.K_v: "cycle_var", pg.K_c: "cycle_val"}
        for i in range(min(9, len(self.app.puzzles))):
            keys[pg.K_1 + i] = f"puzzle:{i}"
        return keys

    def handle(self, event):
        """Xu ly mot su kien pygame; tra ve False khi nguoi dung muon thoat."""
        pg, app = self.pg, self.app
        if event.type == pg.QUIT:
            return False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                return False
            action = self.key_actions().get(event.key)
            if action:
                app.perform(action)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self._on_click(event.pos)
        elif event.type == pg.MOUSEMOTION and self.dragging:
            app.player.jump_fraction(app.timeline.fraction(event.pos[0]))
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        return True

    def _on_click(self, pos):
        app = self.app
        button = app.canvas.button_at(pos)
        if button:
            app.perform(button.action)
        elif app.timeline.contains(pos):
            self.dragging = True
            app.player.jump_fraction(app.timeline.fraction(pos[0]))
        else:
            app.selected = app.board_view.cell_at(pos, app.player.puzzle)
