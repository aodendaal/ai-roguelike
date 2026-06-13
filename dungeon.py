"""
Dungeon generation and layout
"""

import random
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

from constants import (
    MAP_WIDTH, MAP_HEIGHT, DUNGEON_DEPTH, ROOM_MAX_SIZE, ROOM_MIN_SIZE,
    MAX_ROOMS, MAX_MONSTERS_PER_ROOM, MAX_ITEMS_PER_ROOM
)
from monsters import Falcon, Emu
from items import Gold, Potion, Weapon, AmuletOfYendor


class TileType(Enum):
    WALL = 0
    FLOOR = 1
    CLOSED_DOOR = 2
    OPEN_DOOR = 3


@dataclass
class Rect:
    """Rectangle for dungeon rooms"""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> Tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersect(self, other: 'Rect') -> bool:
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Dungeon:
    """Represents a single dungeon floor"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = [[TileType.WALL for _ in range(width)] for _ in range(height)]
        self.rooms = []
        self.monsters: List = []
        self.items: List = []
        self.player_spawn = None
        self.stairs_pos = None

    def create_room(self, room: Rect):
        """Carve out a room"""
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                self.tiles[y][x] = TileType.FLOOR

    def create_h_tunnel(self, x1: int, x2: int, y: int):
        """Create horizontal tunnel"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = TileType.FLOOR

    def create_v_tunnel(self, y1: int, y2: int, x: int):
        """Create vertical tunnel"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = TileType.FLOOR

    def generate(self, level: int, potion_colors: dict = None):
        """Generate dungeon layout"""
        self.rooms = []
        self.monsters = []
        self.items = []

        for _ in range(MAX_ROOMS):
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            x = random.randint(0, self.width - w - 1)
            y = random.randint(0, self.height - h - 1)

            new_room = Rect(x, y, x + w, y + h)

            # Check if room intersects with existing rooms
            if any(new_room.intersect(room) for room in self.rooms):
                continue

            self.create_room(new_room)

            if self.rooms:
                # Connect to previous room
                prev_center = self.rooms[-1].center
                new_center = new_room.center

                if random.choice([True, False]):
                    self.create_h_tunnel(prev_center[0], new_center[0], prev_center[1])
                    self.create_v_tunnel(prev_center[1], new_center[1], new_center[0])
                else:
                    self.create_v_tunnel(prev_center[1], new_center[1], prev_center[0])
                    self.create_h_tunnel(prev_center[0], new_center[0], new_center[1])

            self.rooms.append(new_room)

        # Place doors at some room exits (where tunnels intersect room boundaries)
        for room in self.rooms:
            exits = []
            # Left and right walls
            for y in range(room.y1 + 1, room.y2):
                if self.tiles[y][room.x1] == TileType.FLOOR:
                    exits.append((room.x1, y))
                if self.tiles[y][room.x2] == TileType.FLOOR:
                    exits.append((room.x2, y))
            # Top and bottom walls
            for x in range(room.x1 + 1, room.x2):
                if self.tiles[room.y1][x] == TileType.FLOOR:
                    exits.append((x, room.y1))
                if self.tiles[room.y2][x] == TileType.FLOOR:
                    exits.append((x, room.y2))

            for exit_x, exit_y in exits:
                # Place doors at approximately 50% of the room exits
                if random.random() < 0.5:
                    self.tiles[exit_y][exit_x] = TileType.CLOSED_DOOR

        # Place player in first room
        if self.rooms:
            self.player_spawn = self.rooms[0].center

        # Place stairs in last room
        if self.rooms:
            last_room_center = self.rooms[-1].center
            self.stairs_pos = last_room_center

        # Place monsters and items in other rooms
        for room in self.rooms[1:]:
            # Monsters
            num_monsters = random.randint(0, MAX_MONSTERS_PER_ROOM)
            for _ in range(num_monsters):
                x = random.randint(room.x1 + 1, room.x2 - 1)
                y = random.randint(room.y1 + 1, room.y2 - 1)
                monster = random.choice([Falcon(x, y), Emu(x, y)])
                self.monsters.append(monster)

            # Items
            num_items = random.randint(0, MAX_ITEMS_PER_ROOM)
            for _ in range(num_items):
                x = random.randint(room.x1 + 1, room.x2 - 1)
                y = random.randint(room.y1 + 1, room.y2 - 1)

                if level == DUNGEON_DEPTH:
                    # Last level: place amulet in last room
                    if room == self.rooms[-1] and not self.items:
                        self.items.append(AmuletOfYendor(x, y))
                    elif random.random() < 0.3:
                        self.items.append(Weapon(x, y, random.randint(2, 5)))
                    elif random.random() < 0.5:
                        stat = random.choice(["strength", "health"])
                        amount = random.choice([-2, 2, 3, 5])
                        duration = random.randint(13, 38)
                        potion = Potion(x, y, stat, amount, duration)
                        if potion_colors:
                            color_name, rgb = potion_colors[(stat, amount > 0)]
                            potion.color_name = color_name
                            potion.color = rgb
                        self.items.append(potion)
                    else:
                        self.items.append(Gold(x, y, random.randint(5, 20)))
                else:
                    # Other levels
                    if random.random() < 0.4:
                        self.items.append(Weapon(x, y, random.randint(1, 3)))
                    elif random.random() < 0.4:
                        stat = random.choice(["strength", "health"])
                        amount = random.choice([-2, 2, 3, 5])
                        duration = random.randint(3, 8)
                        potion = Potion(x, y, stat, amount, duration)
                        if potion_colors:
                            color_name, rgb = potion_colors[(stat, amount > 0)]
                            potion.color_name = color_name
                            potion.color = rgb
                        self.items.append(potion)
                    else:
                        self.items.append(Gold(x, y, random.randint(5, 20)))

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[y][x] in (TileType.FLOOR, TileType.OPEN_DOOR)
