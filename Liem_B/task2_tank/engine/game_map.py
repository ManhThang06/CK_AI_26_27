class GameMap:
    def __init__(self, width, height, walls, tank_pos, base_pos):
        self.width = width
        self.height = height
        self.walls = walls         
        self.tank_pos = tank_pos    
        self.base_pos = base_pos    

    @staticmethod
    def load(path):
        with open(path, encoding="utf-8") as f:
            return GameMap.parse(f.read())

    @staticmethod
    def parse(text):
        rows = [line.rstrip() for line in text.split("\n") if line.strip()]
        height = len(rows)
        width = len(rows[0])
        walls = set()
        tank_pos = [None, None]
        base_pos = [None, None]
        for y, row in enumerate(rows):
            if len(row) != width:
                raise ValueError("row %d has wrong length" % y)
            for x, ch in enumerate(row):
                if ch == "#":
                    walls.add((x, y))
                elif ch == "1":
                    tank_pos[0] = (x, y)
                elif ch == "2":
                    tank_pos[1] = (x, y)
                elif ch == "A":
                    base_pos[0] = (x, y)
                elif ch == "B":
                    base_pos[1] = (x, y)
                elif ch != ".":
                    raise ValueError("unknown symbol %r" % ch)
        if None in tank_pos or None in base_pos:
            raise ValueError("map needs two tanks and two bases")
        return GameMap(width, height, walls, tank_pos, base_pos)
