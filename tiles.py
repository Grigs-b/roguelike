
class Tile():
    def __init__(self):
        self.x = None
        self.y = None
        self.image = ' '
        self.hazard = False
        self.damage = 0
        self.collision = False
        self.name = "Air"

    def __repr__(self):
        return self.image


class FloorTile(Tile):
    def __init__(self):
        Tile.__init__(self)
        self.collision = False
        self.image = '.'
        self.name = "Floor"

class EntranceTile(Tile):
    def __init__(self):
        Tile.__init__(self)
        self.image = 'e'
        self.name = "Entrance"

class ExitTile(Tile):
    def __init__(self):
        Tile.__init__(self)
        self.image = 'E'
        self.name = "Exit"

class WallTile(Tile):
    def __init__(self):
        Tile.__init__(self)
        self.image = '#'
        self.collision = True
        self.name = "Wall"

class DoorTile(Tile):
    def __init__(self):
        Tile.__init__(self)
        self.image = 'D'
        self.collision = True
        self.name = "Door"

class LockedDoorTile(DoorTile):
    def __init__(self, key):
        Tile.__init__(self)
        self.image = 'L'
        self.collision = True
        self.name = "Locked Door"
        self.key = key

class KeyTile(Tile):
    def __init__(self):
        Tile.__init__(self)
        self.image = 'k'
        self.collision = False
        self.name = "Key"

class TrapTile(Tile):
    def __init__(self, damage):
        Tile.__init__(self)
        self.image = 't'
        self.collision = False
        self.name = "Trap"