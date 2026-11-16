"""Theme: bang mau va co chu cua giao dien."""


class Theme:
    BG = (15, 23, 36)
    PANEL = (24, 36, 53)
    TEXT = (229, 237, 247)
    MUTED = (151, 168, 188)
    EVENT_COLORS = {"start": (183, 199, 221), "assign": (91, 168, 255),
                    "propagate": (71, 205, 184), "contradiction": (255, 111, 117),
                    "backtrack": (255, 186, 91), "solution": (131, 222, 137),
                    "exhausted": (255, 111, 117), "limit": (255, 186, 91)}
    GUESS_INK = (26, 92, 200)         # chu so cua o dang la phep doan
    DEDUCED_INK = (16, 104, 92)       # chu so do lan truyen suy ra
    FONT_SIZES = (13, 15, 17, 20, 24, 30, 38)

    @staticmethod
    def blend(color, other=(255, 255, 255), ratio=.5):
        return tuple(int(ratio * o + (1 - ratio) * c) for c, o in zip(color, other))
