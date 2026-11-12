"""Chay:  python -m task2_tank.gui.app   (tu thu muc chua task2_tank)"""
import os

import pygame

from CK_AI_26_27.Liem_B.task2_tank.engine import Action
from CK_AI_26_27.Liem_B.task2_tank.plugin_loader import AgentLoadError
from CK_AI_26_27.Liem_B.task2_tank.gui.match import Match
from CK_AI_26_27.Liem_B.task2_tank.gui.menu import GameMenu
from CK_AI_26_27.Liem_B.task2_tank.gui.renderer import GameRenderer

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = {pygame.K_UP: Action.MOVE_UP, pygame.K_DOWN: Action.MOVE_DOWN, pygame.K_LEFT: Action.MOVE_LEFT,
        pygame.K_RIGHT: Action.MOVE_RIGHT, pygame.K_SPACE: Action.FIRE, pygame.K_s: Action.STAY}


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 360))
    pygame.display.set_caption("TDTU AI - Tank Battle")
    while True:
        cfg = GameMenu(screen, BASE).run()
        if cfg is None:
            break
        menu = GameMenu(screen, BASE)
        log = []
        try:
            a1, a2 = menu.build(cfg["a1"], log), menu.build(cfg["a2"], log)
        except AgentLoadError as err:
            print("Khong nap duoc agent:", err)
            continue                                  # quay lai menu, khong sap
        match = Match(cfg["map"], a1, a2)
        names = (menu.label(cfg["a1"]), menu.label(cfg["a2"]))
        cs = 48
        screen = pygame.display.set_mode(GameRenderer.size_for(match.state, cs))
        rend = GameRenderer(screen, cs, names)
        clock, quit_all, last_msg = pygame.time.Clock(), False, ""
        while not match.finished() and not quit_all:
            human = None
            for ev in pygame.event.get():             # luon bom event de cua so khong "not responding"
                if ev.type == pygame.QUIT:
                    quit_all = True
                if ev.type == pygame.KEYDOWN and ev.key in KEYS:
                    human = KEYS[ev.key]
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    quit_all = True
            if match.waiting_for_human():
                if human is None:
                    rend.draw(match.state, "Luot cua ban: phim mui ten / SPACE ban / S dung yen")
                    clock.tick(30)
                    continue
                match.step(human)
            else:
                last_msg = "%s: %s" % ("MAX" if match.state.player() == 0 else "MIN", match.step().name)
                clock.tick(6)
            rend.draw(match.state, last_msg + ("  | " + log[-1] if log else ""))
        if not quit_all:
            msg = match.result_text()
            match.save_log(os.path.join(BASE, "logs", "last_match.csv"))
            rend.draw(match.state, msg + " - ESC/dong cua so de ve menu")
            waiting = True
            while waiting:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        quit_all = waiting = False
                        pygame.quit()
                        return
                    if ev.type == pygame.KEYDOWN:
                        waiting = False
        if quit_all:
            break
        screen = pygame.display.set_mode((640, 360))
    pygame.quit()


if __name__ == "__main__":
    main()
