'''
Using whatever languages, frameworks and libraries you choose write a Roguelike dungeon generator. (http://en.wikipedia.org/wiki/Roguelike)
Your system should generate random but sensible dungeons
 - e.g. there should not be isolated areas that are unreachable and there should be an entrance and exit.

The presentation of your dungeons is up to you. Take the implementation as far as you'd like. Some ideas:
- generate dungeons with provided x/y dimensions
- treasures
- monsters
- locked doors w/ accessible keys
- other terrain types
- obstacles (fire, water, pits, traps)

Please don't spend more than one working day on your solution.
Provide a brief README detailing how to build and run your project.
Ideally share your project via Github.
'''
import random
from tiles import Tile, WallTile, FloorTile, DoorTile, EntranceTile, ExitTile

# split out to config
ROOM_MIN_SIZE = 6
ROOM_MAX_SIZE = 10
MIN_DOORS_PER_ROOM = 1
MAX_DOORS_PER_ROOM = 2
MIN_PATHS_PER_DOOR = 1
MAX_PATHS_PER_DOOR = 2
CHANCE_DOOR_LOCKED = .4
MAX_PLACEMENT_ATTEMPTS = 200
CHANCE_FOR_MONSTER = .3
CHANCE_FOR_LOOT = .05


class Room():

    def __init__(self, topleft, bottomright):
        self.topleft = topleft
        self.bottomright = bottomright
        self.x1 = topleft.x
        self.y1 = topleft.y
        self.x2 = bottomright.x
        self.y2 = bottomright.y

    def _range_overlap(self, a_min, a_max, b_min, b_max):
        '''Neither range is completely greater than the other
        '''
        return (a_min <= b_max) and (b_min <= a_max)

    def intersects(self, room):
        '''Overlapping rectangles overlap both horizontally & vertically
        '''
        return self._range_overlap(self.x1, self.x2, room.x1, room.x2) and self._range_overlap(self.y1, self.y2, room.y1, room.y2)


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "Point({},{})".format(self.x,self.y)

    def __eq__(self, obj):
        return self.x == obj.x and self.y == obj.y

    def __hash__(self):
        return hash((self.x, self.y))


class Dungeon():
    def __init__(self, width, height, density=.10, rooms=[], doors=[], mobs=[]):
        self.width = width
        self.height = height
        self.density = density
        # developer note: home of the most hateful bug that stressed me out to no end :)
        #self.tiles = [[Tile()]*width]*height
        self.tiles = [[WallTile() for i in range(width)] for j in range(height)]
        self.entrance = None
        self.exit = None
        self.rooms = rooms
        self.doors = doors
        self.mobs = mobs
        self.generate()

    def __repr__(self):
        # prettifies the print a bit
        # todo remove enumerates once debugged
        return '\n'.join([''.join(['{:2}'.format(item) for x, item in enumerate(row)]) for y, row in enumerate(self.tiles)])

    def load_configuration(config):
        #set parameters from configuration
        pass

    def clear(self):
        self.tiles = [[WallTile() for i in range(self.width)] for j in range(self.height)]
        self.entrance = None
        self.exit = None
        self.keys = {}

    def generate(self):
        self.clear()
        print('Generating Dungeon')
        # create rooms
        attempts = 0
        while self.should_add_room() and attempts < MAX_PLACEMENT_ATTEMPTS:
            x1 = random.randint(1, self.width-ROOM_MIN_SIZE)
            y1 = random.randint(1, self.height-ROOM_MIN_SIZE)
            x2 = min(x1+random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), self.width-1)
            y2 = min(y1+random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), self.height-1)
            topleft = Point(x1, y1)
            bottomright = Point(x2, y2)

            if self.valid_room(topleft, bottomright):
                current_room = Room(topleft, bottomright)
                print('Attempting to add room at ({},{}),({},{})'.format(x1, y1, x2, y2))
                self.rooms.append(current_room)
                self.fill_with_tile(topleft, bottomright, FloorTile)
                self.add_walls(topleft, bottomright)
                if not self.entrance:
                    room = random.choice(self.rooms)
                    self.entrance = self.place_in_room(room, EntranceTile)
                walls = self.get_tiles_in_bounds(topleft, bottomright, WallTile)
                # remove corner pieces so we dont add doors to those
                for corner in [topleft, bottomright, Point(topleft.x, bottomright.y), Point(bottomright.x, topleft.y)]:
                    if corner in walls:
                        walls.remove(corner)
                self.add_doors(walls)
                self.add_mobs()
            attempts += 1

        #place exit
        if not self.exit:
            room = random.choice(self.rooms)
            self.entrance = self.place_in_room(room, ExitTile)

        #connect our rooms
        self.create_paths()

        self.add_traps()
        self.add_hazards()
        return


    def should_add_room(self):
        # if the amount of room tiles exceeds the percentage of total tiles specified by
        #   density, return False, else return True
        return len(self.get_tiles(FloorTile)) < (self.width*self.height) * self.density

    def valid_room(self, topleft, bottomright):
        #check bounds
        if topleft.x <= 0 or topleft.y <= 0:
            return False
        if bottomright.x >= self.width or bottomright.y >= self.height:
            return False

        #print('Ranging: x:{}, y:{}'.format(range(topleft.x-1, bottomright.x+2), range(topleft.y-1, bottomright.y+2)))
        for row in range(topleft.y-1, min(bottomright.y+2, self.height-1)):
            for col in range(topleft.x-1, min(bottomright.x+2, self.width-1)):
                if not self.is_wall(row, col) or not self.is_empty(row, col):
                    return False

        #check to make sure that all tiles within the room are walls presently
        return True

    def is_tile(self, row, col, tile):
        if col >= self.width or row >= self.height:
            return False
        return isinstance(self.tiles[row][col], tile)

    def is_empty(self, row, col):
        return self.is_tile(row, col, Tile)

    def is_wall(self, row, col):
        return self.is_tile(row, col, WallTile)

    def fill_with_tile(self, topleft, bottomright, tile):
        for row in range(topleft.y, bottomright.y+1):
            for col in range(topleft.x, bottomright.x+1):
                self.tiles[row][col] = tile()

    def add_walls(self, topleft, bottomright):

        for x in range(topleft.x, bottomright.x+1):
            self.tiles[topleft.y][x] = WallTile()
            self.tiles[bottomright.y][x] = WallTile()

        for y in range(topleft.y, bottomright.y+1):
            self.tiles[y][topleft.x] = WallTile()
            self.tiles[y][bottomright.x] = WallTile()

    def add_doors(self, walls):
        num_doors = random.randint(MIN_DOORS_PER_ROOM, MAX_DOORS_PER_ROOM)
        points = random.sample(walls, num_doors)
        for point in points:
            self.tiles[point.y][point.x] = DoorTile()

            self.doors.append(point)

    def place_in_room(self, room, tile):
        row, col = self.get_point_in_bounds(room.topleft, room.bottomright)
        self.tiles[row][col] = tile()
        return row, col

    def get_point_in_bounds(self, topleft, bottomright):
        col = random.randint(topleft.x, bottomright.x)
        row = random.randint(topleft.y, bottomright.y)
        return row, col

    def create_paths(self):
        for door in self.doors:
            connect_to = [door]
            # make sure every door gets at least one connection, and make sure a connection doesnt include itself
            # todo: or another door in the same room
            while door in connect_to:
                connect_to = set(random.sample(self.doors, random.randint(MIN_PATHS_PER_DOOR, MAX_PATHS_PER_DOOR)))
            for connection in connect_to:
                #choose the spot opposite the room to start the door
                self.connect_path(self.tiles, door.x, door.y, connection.x, connection.y)

    def connect_path(self, tiles, currx, curry, goalx, goaly):
        if currx == goalx and curry == goaly:
            return tiles

        if currx >= self.width or curry >= self.height or currx < 0 or curry < 0:
            return tiles

        # look for padding on the sides so that we dont make hallways right against the side of our rooms

        movex = random.choice([True, False])
        if movex:
            if self.is_wall(curry, currx) and \
                    (self.is_wall(curry-1, currx) or self.is_tile(curry-1, currx, DoorTile)) and \
                    (self.is_wall(curry+1, currx) or self.is_tile(curry+1, currx, DoorTile)):
                tiles[curry][currx] = FloorTile()
            if currx < goalx:
                self.connect_path(tiles, currx+1, curry, goalx, goaly)
            else:
                self.connect_path(tiles, currx-1, curry, goalx, goaly)
        else:
            if self.is_wall(curry, currx) and \
                    (self.is_wall(curry, currx-1) or self.is_tile(curry, currx-1, DoorTile)) and \
                    (self.is_wall(curry, currx+1) or self.is_tile(curry, currx+1, DoorTile)):
                tiles[curry][currx] = FloorTile()
            if curry < goaly:
                self.connect_path(tiles, currx, curry+1, goalx, goaly)
            else:
                self.connect_path(tiles, currx, curry-1, goalx, goaly)

        return tiles

    def get_tiles_in_bounds(self, topleft, bottomright, tile_type):
        tiles = []
        for y in range(topleft.y, bottomright.y+1):
            for x in range(topleft.x, bottomright.x+1):
                if isinstance(self.tiles[y][x], tile_type):
                    tiles.append(Point(x, y))
        return tiles

    def get_tiles(self, tile_type):
        return self.get_tiles_in_bounds(Point(0, 0), Point(self.width-1, self.height-1), tile_type)

    def add_mobs(self):
        pass

    def add_traps(self):
        pass

    def add_hazards(self):
        pass

if __name__ == '__main__':
    #set seed for testing
    #random.seed(9001)
    d = Dungeon(50, 50)
    print(d)
