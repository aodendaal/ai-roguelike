"""
Main game logic and rendering
"""

import tcod
import numpy as np
from enum import Enum

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT, 
    DUNGEON_DEPTH, FOV_RADIUS, VERSION
)
from entities import Player
from dungeon import Dungeon, TileType
from leaderboard import Leaderboard
from items import Potion, Weapon

class GameState(Enum):
    MENU = 1
    ENTERING_NAME = 2
    PLAYING = 3
    PLAYER_DEAD = 4
    GAME_WON = 5
    VIEW_LEADERBOARD = 6
    INVENTORY = 7
    QUAFF_MENU = 8


class Game:
    """Main game class"""
    def __init__(self):
        self.console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
        self.context = None
        self.player = Player(0, 0)
        self.dungeon = None
        self._state = GameState.MENU
        self.visible = None
        self.explored = None
        self.message_log = []
        self.turn_count = 0
        self.death_cause = None  # Track which monster killed the player
        self.leaderboard = Leaderboard()
        self.input_buffer = ""  # For name input
        self.player_name = ""
        self.potions_drunk = 0
        self.weapons_picked_up = 0
        self.doors_opened = 0
        self.monsters_killed = 0
        self.floors_descended = 0
        self.potion_colors = {}

    @property
    def state(self) -> GameState:
        return self._state

    @state.setter
    def state(self, value: GameState):
        old_state = getattr(self, "_state", None)
        self._state = value
        if self.context and hasattr(self.context, "sdl_window") and self.context.sdl_window:
            if value == GameState.ENTERING_NAME and old_state != GameState.ENTERING_NAME:
                self.context.sdl_window.start_text_input()
            elif old_state == GameState.ENTERING_NAME and value != GameState.ENTERING_NAME:
                self.context.sdl_window.stop_text_input()

    @property
    def entering_name(self) -> bool:
        return self.state == GameState.ENTERING_NAME

    @entering_name.setter
    def entering_name(self, value: bool):
        if value:
            self.state = GameState.ENTERING_NAME
        else:
            self.state = GameState.PLAYING

    def new_game(self):
        """Start a new game"""
        self.player = Player(0, 0)
        self.player.current_level = 1
        self.player.has_amulet = False
        self.message_log = []
        self.turn_count = 0
        self.potions_drunk = 0
        self.weapons_picked_up = 0
        self.doors_opened = 0
        self.monsters_killed = 0
        self.floors_descended = 0
        
        # Shuffle and assign random colors to potion types each run
        import random
        color_pool = [
            ("red", (255, 50, 50)),
            ("blue", (50, 50, 255)),
            ("green", (50, 255, 50)),
            ("yellow", (255, 255, 50)),
            ("purple", (200, 50, 200)),
            ("orange", (255, 150, 50)),
            ("cyan", (50, 255, 255)),
            ("pink", (255, 150, 200)),
        ]
        random.shuffle(color_pool)
        self.potion_colors = {
            ("strength", True): color_pool[0],   # buff
            ("strength", False): color_pool[1],  # debuff
            ("health", True): color_pool[2],
            ("health", False): color_pool[3],
        }

        self._state = GameState.PLAYING
        self.death_cause = None
        self.load_level(1)
        self.add_message("Welcome to the Roguelike Dungeon!")
        self.add_message("Find the Amulet of Yendor on the 5th level and escape!")

    def start_game_with_name(self, name: str):
        """Initialize game stats and start the game with the given player name"""
        self.player_name = name
        self.new_game()
        self.state = GameState.PLAYING

    def load_level(self, level: int):
        """Load a dungeon level"""
        self.player.current_level = level
        self.dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT)
        self.dungeon.generate(level, self.potion_colors)

        # Place player
        if self.dungeon.player_spawn:
            self.player.x, self.player.y = self.dungeon.player_spawn

        # Initialize FOV arrays
        self.visible = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
        self.explored = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)

        self.add_message(f"Entered level {level}")

    def add_message(self, text: str):
        """Add a message to the log"""
        self.message_log.append(text)
        if len(self.message_log) > 3:
            self.message_log.pop(0)

    def get_floor_colors(self) -> dict:
        """Get the wall and floor pastel colors for the current floor level"""
        palettes = {
            1: { # Soft Lavender/Purple
                "wall_visible": (150, 140, 180),
                "floor_visible": (200, 190, 220),
                "wall_explored": (75, 70, 90),
                "floor_explored": (100, 95, 110),
            },
            2: { # Soft Mint/Green
                "wall_visible": (130, 170, 140),
                "floor_visible": (180, 210, 190),
                "wall_explored": (65, 85, 70),
                "floor_explored": (90, 105, 95),
            },
            3: { # Soft Sky Blue
                "wall_visible": (130, 160, 180),
                "floor_visible": (180, 205, 220),
                "wall_explored": (65, 80, 90),
                "floor_explored": (90, 102, 110),
            },
            4: { # Soft Peach/Orange
                "wall_visible": (180, 145, 130),
                "floor_visible": (220, 195, 180),
                "wall_explored": (90, 72, 65),
                "floor_explored": (110, 97, 90),
            },
            5: { # Soft Rose/Pink
                "wall_visible": (180, 135, 150),
                "floor_visible": (220, 185, 195),
                "wall_explored": (90, 67, 75),
                "floor_explored": (110, 92, 97),
            }
        }
        level = self.player.current_level
        if level not in palettes:
            wrapped_level = ((level - 1) % 5) + 1
            return palettes[wrapped_level]
        return palettes[level]

    def compute_fov(self):
        """Compute field of view using simple line-of-sight"""
        self.visible.fill(False)
        # Simple circular FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                dx = x - self.player.x
                dy = y - self.player.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= FOV_RADIUS:
                    # Simple line of sight check
                    if self._is_visible(self.player.x, self.player.y, x, y):
                        self.visible[y, x] = True
                        self.explored[y, x] = True

    def _is_visible(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Simple line-of-sight check using Bresenham's line algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x2 > x1 else -1
        sy = 1 if y2 > y1 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            if x == x2 and y == y2:
                return True
                
            if not self.dungeon.is_walkable(x, y) and (x, y) != (x1, y1):
                return False
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy



    def move_player(self, dx: int, dy: int):
        """Move player and handle interactions"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy

        if not self.dungeon.is_walkable(new_x, new_y):
            # Check for closed door
            if (0 <= new_x < self.dungeon.width and 0 <= new_y < self.dungeon.height and
                    self.dungeon.tiles[new_y][new_x] == TileType.CLOSED_DOOR):
                self.dungeon.tiles[new_y][new_x] = TileType.OPEN_DOOR
                self.add_message("You open the door.")
                self.doors_opened += 1
                self.update_game()
            return

        # Check for monsters
        for monster in self.dungeon.monsters:
            if monster.x == new_x and monster.y == new_y:
                damage = self.player.attack(monster)
                self.add_message(f"Hit {monster.name} for {damage} damage!")
                if monster.health <= 0:
                    self.dungeon.monsters.remove(monster)
                    self.add_message(f"{monster.name} died!")
                    self.monsters_killed += 1
                return

        # Move player
        self.player.move(dx, dy)

        # Check for items (auto-pickup for non-potions only)
        items_to_remove = []
        for item in self.dungeon.items:
            if item.x == self.player.x and item.y == self.player.y:
                if not isinstance(item, Potion):
                    msg = item.pick_up(self.player)
                    if isinstance(item, Weapon):
                        self.weapons_picked_up += 1
                    self.add_message(msg)
                    items_to_remove.append(item)

        for item in items_to_remove:
            self.dungeon.items.remove(item)

    def pickup_item(self):
        """Pick up an item at the player's position"""
        item_to_pick = None
        for item in self.dungeon.items:
            if item.x == self.player.x and item.y == self.player.y:
                item_to_pick = item
                break
                
        if item_to_pick:
            msg = item_to_pick.pick_up(self.player)
            self.add_message(msg)
            self.dungeon.items.remove(item_to_pick)
            if isinstance(item_to_pick, Weapon):
                self.weapons_picked_up += 1
            self.update_game()
        else:
            self.add_message("There is nothing here to pick up.")

    def update_game(self):
        """Update game state after player turn"""
        # Update player status effects
        self.player.update_status_effects()

        # Monster AI
        self.compute_fov()

        for monster in self.dungeon.monsters:
            if self.visible[monster.y, monster.x]:
                # Simple chase AI
                dx = 0
                dy = 0
                if monster.x < self.player.x:
                    dx = 1
                elif monster.x > self.player.x:
                    dx = -1

                if monster.y < self.player.y:
                    dy = 1
                elif monster.y > self.player.y:
                    dy = -1

                new_x = monster.x + dx
                new_y = monster.y + dy

                if (new_x, new_y) == (self.player.x, self.player.y):
                    # Attack player
                    damage = monster.attack(self.player)
                    self.add_message(f"{monster.name} hits you for {damage} damage!")
                    self.death_cause = monster.name  # Track what killed the player
                elif self.dungeon.is_walkable(new_x, new_y):
                    monster.move(dx, dy)

        self.turn_count += 1

        # Check win/lose conditions
        if self.player.health <= 0:
            self.state = GameState.PLAYER_DEAD
            self.add_message("You died!")
            self.save_score()

    def render(self):
        """Render the game to the console"""
        self.console.clear()

        if self.state == GameState.MENU:
            self.console.print(SCREEN_WIDTH // 2 - 12, SCREEN_HEIGHT // 2 - 4, "=== ROGUELIKE DUNGEON ===", (255, 215, 0))
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 - 1, "1. Play New Game", (200, 200, 200))
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 + 1, "2. View Leaderboard", (200, 200, 200))
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 + 3, "3. Exit", (200, 200, 200))
            version_str = f"v{VERSION}"
            self.console.print(SCREEN_WIDTH - len(version_str) - 2, SCREEN_HEIGHT - 2, version_str, (100, 100, 100))
            
        elif self.state == GameState.VIEW_LEADERBOARD:
            self.console.print(SCREEN_WIDTH // 2 - 10, 4, "=== LEADERBOARD ===", (255, 215, 0))
            
            top_entries = self.leaderboard.get_top_entries(10)
            start_y = 7
            
            headers = f"{'Rank':4} | {'Name':20} | {'Level':9} | {'Gold':5} | {'Result'}"
            self.console.print(5, start_y, headers, (255, 215, 0))
            self.console.print(5, start_y + 1, "-" * 70, (150, 150, 150))
            
            for idx, entry in enumerate(top_entries):
                y = start_y + 2 + idx
                
                # Highlight current player's entry if it matches
                is_current = False
                if self.player_name:
                    is_current = (entry.player_name == self.player_name and
                                  entry.gold == self.player.gold and
                                  entry.level == self.player.current_level)
                
                entry_color = (100, 255, 100) if is_current else (200, 200, 200)
                
                result = "WON - Found Amulet" if entry.outcome == "won" else f"DIED - {entry.death_cause}"
                rank_str = f"{idx + 1:2}."
                line = f"{rank_str:4} | {entry.player_name:20} | Level {entry.level}/5 | {entry.gold:5} | {result}"
                self.console.print(5, y, line, entry_color)
                
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT - 4, "Press Escape to return to menu", (150, 150, 150))
            
        elif self.state == GameState.ENTERING_NAME:
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 - 4, "=== NEW CHARACTER ===", (255, 215, 0))
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 - 1, "Enter your name:", (255, 255, 255))
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 + 1, self.input_buffer + "_", (200, 255, 200))
            self.console.print(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 + 3, "Press Enter to start, Escape to cancel", (150, 150, 150))
            
    def render_playing_screen(self):
        # Compute FOV
        self.compute_fov()

        # Get pastel colors for the current level
        colors = self.get_floor_colors()

        # Draw map
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                tile = self.dungeon.tiles[y][x]
                if self.visible[y, x]:
                    if tile == TileType.WALL:
                        self.console.print(x, y, '#', colors["wall_visible"])
                    elif tile == TileType.CLOSED_DOOR:
                        self.console.print(x, y, '+', (139, 90, 43))
                    elif tile == TileType.OPEN_DOOR:
                        self.console.print(x, y, '/', (139, 90, 43))
                    else:  # Floor
                        self.console.print(x, y, '.', colors["floor_visible"])
                elif self.explored[y, x]:
                    if tile == TileType.WALL:
                        self.console.print(x, y, '#', colors["wall_explored"])
                    elif tile == TileType.CLOSED_DOOR:
                        self.console.print(x, y, '+', (80, 50, 25))
                    elif tile == TileType.OPEN_DOOR:
                        self.console.print(x, y, '/', (80, 50, 25))
                    else:  # Floor
                        self.console.print(x, y, '.', colors["floor_explored"])

        # Draw stairs
        if self.visible[self.dungeon.stairs_pos[1], self.dungeon.stairs_pos[0]]:
            self.console.print(self.dungeon.stairs_pos[0], self.dungeon.stairs_pos[1],
                             '>', (200, 200, 200))

        # Draw items
        for item in self.dungeon.items:
            if self.visible[item.y, item.x]:
                self.console.print(item.x, item.y, item.char, item.color)

        # Draw monsters
        for monster in self.dungeon.monsters:
            if self.visible[monster.y, monster.x]:
                self.console.print(monster.x, monster.y, monster.char, monster.color)

        # Draw player
        self.console.print(self.player.x, self.player.y, self.player.char, self.player.color)

        # Draw UI
        ui_y = MAP_HEIGHT
        ui_text = f"Level: {self.player.current_level}/5 | HP: {self.player.health}/{self.player.max_health} | STR: {self.player.current_strength} | Gold: {self.player.gold}"
        self.console.print(0, ui_y, ui_text, (255, 255, 255))

        ui_y += 1
        for i, msg in enumerate(self.message_log):
            self.console.print(0, ui_y + i, msg, (200, 200, 200))

    def render(self):
        """Render the game to the console"""
        self.console.clear()

        if self.state == GameState.MENU:
            self.console.print(SCREEN_WIDTH // 2 - 12, SCREEN_HEIGHT // 2 - 4, "=== ROGUELIKE DUNGEON ===", (255, 215, 0))
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 - 1, "1. Play New Game", (200, 200, 200))
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 + 1, "2. View Leaderboard", (200, 200, 200))
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2 + 3, "3. Exit", (200, 200, 200))
            version_str = f"v{VERSION}"
            self.console.print(SCREEN_WIDTH - len(version_str) - 2, SCREEN_HEIGHT - 2, version_str, (100, 100, 100))
            
        elif self.state == GameState.VIEW_LEADERBOARD:
            self.console.print(SCREEN_WIDTH // 2 - 10, 4, "=== LEADERBOARD ===", (255, 215, 0))
            
            top_entries = self.leaderboard.get_top_entries(10)
            start_y = 7
            
            headers = f"{'Rank':4} | {'Name':20} | {'Level':9} | {'Gold':5} | {'Result'}"
            self.console.print(5, start_y, headers, (255, 215, 0))
            self.console.print(5, start_y + 1, "-" * 70, (150, 150, 150))
            
            for idx, entry in enumerate(top_entries):
                y = start_y + 2 + idx
                
                # Highlight current player's entry if it matches
                is_current = False
                if self.player_name:
                    is_current = (entry.player_name == self.player_name and
                                  entry.gold == self.player.gold and
                                  entry.level == self.player.current_level)
                
                entry_color = (100, 255, 100) if is_current else (200, 200, 200)
                
                result = "WON - Found Amulet" if entry.outcome == "won" else f"DIED - {entry.death_cause}"
                rank_str = f"{idx + 1:2}."
                line = f"{rank_str:4} | {entry.player_name:20} | Level {entry.level}/5 | {entry.gold:5} | {result}"
                self.console.print(5, y, line, entry_color)
                
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT - 4, "Press Escape to return to menu", (150, 150, 150))
            
        elif self.state == GameState.ENTERING_NAME:
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 - 4, "=== NEW CHARACTER ===", (255, 215, 0))
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 - 1, "Enter your name:", (255, 255, 255))
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 + 1, self.input_buffer + "_", (200, 255, 200))
            self.console.print(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 + 3, "Press Enter to start, Escape to cancel", (150, 150, 150))
            
        elif self.state == GameState.PLAYING:
            self.render_playing_screen()

        elif self.state in (GameState.INVENTORY, GameState.QUAFF_MENU):
            self.render_playing_screen()
            
            # Center overlay box
            box_width = 40
            box_height = 20
            box_x = (SCREEN_WIDTH - box_width) // 2
            box_y = (SCREEN_HEIGHT - box_height) // 2
            
            # Fill background
            for y in range(box_y, box_y + box_height):
                for x in range(box_x, box_x + box_width):
                    self.console.print(x, y, " ", bg=(0, 0, 0))
            
            # Border
            for x in range(box_x, box_x + box_width):
                self.console.print(x, box_y, "-", (255, 255, 255))
                self.console.print(x, box_y + box_height - 1, "-", (255, 255, 255))
            for y in range(box_y, box_y + box_height):
                self.console.print(box_x, y, "|", (255, 255, 255))
                self.console.print(box_x + box_width - 1, y, "|", (255, 255, 255))
                
            title = " INVENTORY " if self.state == GameState.INVENTORY else " QUAFF POTION "
            self.console.print(box_x + (box_width - len(title)) // 2, box_y, title, (255, 215, 0))
            
            # List items
            if not self.player.inventory:
                self.console.print(box_x + 2, box_y + 2, "Your inventory is empty.", (150, 150, 150))
            else:
                for idx, item in enumerate(self.player.inventory):
                    char_code = chr(ord('a') + idx)
                    desc = item.get_description()
                    item_str = f"({char_code}) {desc}"
                    self.console.print(box_x + 2, box_y + 2 + idx, item_str, (200, 200, 200))
                    
            # Instructions
            if self.state == GameState.INVENTORY:
                footer = "Press Escape or I to close"
            else:
                footer = "Select letter to drink, Esc to cancel"
            self.console.print(box_x + (box_width - len(footer)) // 2, box_y + box_height - 2, footer, (150, 150, 150))

        elif self.state in (GameState.PLAYER_DEAD, GameState.GAME_WON):
            # Clear console to draw a clean character status screen
            self.console.clear()
            
            header = "YOU DIED!" if self.state == GameState.PLAYER_DEAD else "YOU WON!"
            header_color = (255, 0, 0) if self.state == GameState.PLAYER_DEAD else (0, 255, 0)
            self.console.print(SCREEN_WIDTH // 2 - len(header) // 2, 5, header, header_color)
            
            self.console.print(SCREEN_WIDTH // 2 - 12, 8, "=== CHARACTER STATUS ===", (255, 215, 0))
            
            # Print stats
            stats = [
                f"Character Name:   {self.player_name}",
                f"Turns Played:     {self.turn_count}",
                f"Gold Collected:   {self.player.gold}",
                f"Floors Descended: {self.floors_descended}",
                f"Potions Drunk:    {self.potions_drunk}",
                f"Weapons Picked:   {self.weapons_picked_up}",
                f"Doors Opened:     {self.doors_opened}",
                f"Monsters Killed:  {self.monsters_killed}"
            ]
            
            start_y = 11
            for i, stat in enumerate(stats):
                self.console.print(SCREEN_WIDTH // 2 - 15, start_y + i, stat, (200, 200, 200))
                
            footer_y = SCREEN_HEIGHT - 6
            self.console.print(SCREEN_WIDTH // 2 - 22, footer_y,
                             "Press Enter to view Leaderboard", (100, 255, 100))
            self.console.print(SCREEN_WIDTH // 2 - 22, footer_y + 2,
                             "Press R to return to menu or Q to quit", (150, 150, 150))

        self.context.present(self.console)

    def process_events(self) -> bool:
        """Process all pending events. Returns False to exit the game."""
        for event in tcod.event.get():
            if isinstance(event, tcod.event.Quit):
                return False
                
            if self.state == GameState.MENU:
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.N1, tcod.event.KeySym.KP_1):
                        self.input_buffer = ""
                        self.state = GameState.ENTERING_NAME
                    elif event.sym in (tcod.event.KeySym.N2, tcod.event.KeySym.KP_2):
                        self.leaderboard.load()
                        self.state = GameState.VIEW_LEADERBOARD
                    elif event.sym in (tcod.event.KeySym.N3, tcod.event.KeySym.KP_3, tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
                        return False
                        
            elif self.state == GameState.VIEW_LEADERBOARD:
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.RETURN, tcod.event.KeySym.SPACE):
                        self.state = GameState.MENU
                        
            elif self.state == GameState.ENTERING_NAME:
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym == tcod.event.KeySym.RETURN:
                        if self.input_buffer.strip():
                            self.start_game_with_name(self.input_buffer.strip())
                    elif event.sym == tcod.event.KeySym.BACKSPACE:
                        self.input_buffer = self.input_buffer[:-1]
                    elif event.sym == tcod.event.KeySym.ESCAPE:
                        self.state = GameState.MENU
                elif isinstance(event, tcod.event.TextInput):
                    if len(self.input_buffer) < 20:
                        self.input_buffer += event.text
                        
            elif self.state == GameState.PLAYING:
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym == tcod.event.KeySym.ESCAPE:
                        self.state = GameState.MENU
                        return True
                    elif event.sym == tcod.event.KeySym.UP:
                        self.move_player(0, -1)
                    elif event.sym == tcod.event.KeySym.DOWN:
                        self.move_player(0, 1)
                    elif event.sym == tcod.event.KeySym.LEFT:
                        self.move_player(-1, 0)
                    elif event.sym == tcod.event.KeySym.RIGHT:
                        self.move_player(1, 0)
                    elif event.sym == tcod.event.KeySym.PERIOD:
                        # Try to go down stairs
                        if self.dungeon.stairs_pos and (self.player.x, self.player.y) == self.dungeon.stairs_pos:
                            if self.player.current_level < DUNGEON_DEPTH:
                                self.load_level(self.player.current_level + 1)
                                self.floors_descended += 1
                            elif self.player.has_amulet:
                                self.state = GameState.GAME_WON
                                self.save_score()
                                return True
                            else:
                                self.add_message("You need the Amulet of Yendor first!")
                        else:
                            self.add_message("No stairs here!")
                    elif event.sym == tcod.event.KeySym.COMMA:
                        self.pickup_item()
                    elif event.sym == tcod.event.KeySym.i:
                        self.state = GameState.INVENTORY
                    elif event.sym == tcod.event.KeySym.q:
                        self.state = GameState.QUAFF_MENU
                    self.update_game()
                    
            elif self.state == GameState.INVENTORY:
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.i):
                        self.state = GameState.PLAYING
                        
            elif self.state == GameState.QUAFF_MENU:
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym == tcod.event.KeySym.ESCAPE:
                        self.state = GameState.PLAYING
                    else:
                        key_char = None
                        if tcod.event.KeySym.a <= event.sym <= tcod.event.KeySym.z:
                            key_char = chr(ord('a') + (event.sym - tcod.event.KeySym.a))
                        
                        if key_char:
                            idx = ord(key_char) - ord('a')
                            if 0 <= idx < len(self.player.inventory):
                                item = self.player.inventory[idx]
                                if isinstance(item, Potion):
                                    msg = item.quaff(self.player)
                                    self.add_message(msg)
                                    self.potions_drunk += 1
                                    self.player.inventory.pop(idx)
                                    self.state = GameState.PLAYING
                                    self.update_game()
                    
            elif self.state in (GameState.PLAYER_DEAD, GameState.GAME_WON):
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                        self.leaderboard.load()
                        self.state = GameState.VIEW_LEADERBOARD
                    elif event.sym == tcod.event.KeySym.R:
                        self.state = GameState.MENU
                    elif event.sym in (tcod.event.KeySym.Q, tcod.event.KeySym.ESCAPE):
                        return False
        return True

    def handle_input(self) -> bool:
        """Handle player input. Provided for test compatibility."""
        return self.process_events()

    def game_over_input(self) -> bool:
        """Handle game over input. Provided for test compatibility."""
        return self.process_events()

    def save_score(self):
        """Save the current score to the leaderboard"""
        player_name = self.player_name.strip() if getattr(self, "player_name", None) else "Anonymous"
        outcome = "won" if self.state == GameState.GAME_WON else "died"
        
        self.leaderboard.add_entry(
            player_name=player_name,
            gold=self.player.gold,
            level=self.player.current_level,
            outcome=outcome,
            death_cause=self.death_cause
        )

    def load_tileset(self):
        """Try to load custom tileset, fall back to default if not available"""
        try:
            import sys
            import pathlib
            from PIL import Image
            
            # Use sys._MEIPASS if running as a PyInstaller bundle
            if hasattr(sys, "_MEIPASS"):
                base_path = pathlib.Path(sys._MEIPASS)
            else:
                base_path = pathlib.Path(__file__).parent
                
            tileset_path = base_path / "deja10x10_gs_tc.png"
            if tileset_path.exists():
                # Scale the tileset by 1.5x (50% bigger) using Nearest Neighbor to keep pixel art clean
                with Image.open(tileset_path) as img:
                    new_width = int(img.width * 1.5)
                    new_height = int(img.height * 1.5)
                    resized_img = img.resize((new_width, new_height), Image.Resampling.NEAREST)
                    temp_path = base_path / "deja10x10_gs_tc_scaled.png"
                    resized_img.save(temp_path)
                return tcod.tileset.load_tilesheet(
                    temp_path, 32, 8, tcod.tileset.CHARMAP_TCOD
                )
        except Exception as e:
            print(f"Could not load custom tileset: {e}")
        return None

    def run(self):
        """Main game loop"""
        tileset = self.load_tileset()
        
        # Use custom tileset if loaded, otherwise default
        ctx_kwargs = {
            "columns": SCREEN_WIDTH,
            "rows": SCREEN_HEIGHT,
            "title": "Roguelike Dungeon",
            "vsync": True,
        }
        if tileset:
            ctx_kwargs["tileset"] = tileset
        
        with tcod.context.new(**ctx_kwargs) as self.context:
            self.state = GameState.MENU
            
            while True:
                self.render()
                if not self.process_events():
                    break
