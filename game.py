"""
Main game logic and rendering
"""

import tcod
import numpy as np
from enum import Enum

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT, 
    DUNGEON_DEPTH, FOV_RADIUS
)
from entities import Player
from dungeon import Dungeon
from leaderboard import Leaderboard

class GameState(Enum):
    PLAYING = 1
    PLAYER_DEAD = 2
    GAME_WON = 3


class Game:
    """Main game class"""
    def __init__(self):
        self.console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
        self.context = None
        self.player = Player(0, 0)
        self.dungeon = None
        self.state = GameState.PLAYING
        self.visible = None
        self.explored = None
        self.message_log = []
        self.turn_count = 0
        self.death_cause = None  # Track which monster killed the player
        self.leaderboard = Leaderboard()
        self.input_buffer = ""  # For name input
        self.entering_name = False  # Flag for name entry mode

    def new_game(self):
        """Start a new game"""
        self.player = Player(0, 0)
        self.player.current_level = 1
        self.player.has_amulet = False
        self.message_log = []
        self.turn_count = 0
        self.state = GameState.PLAYING
        self.death_cause = None
        self.input_buffer = ""
        self.entering_name = False
        self.load_level(1)
        self.add_message("Welcome to the Roguelike Dungeon!")
        self.add_message("Find the Amulet of Yendor on the 5th level and escape!")

    def load_level(self, level: int):
        """Load a dungeon level"""
        self.player.current_level = level
        self.dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT)
        self.dungeon.generate(level)

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
            if not self.dungeon.is_walkable(x, y) and (x, y) != (x1, y1):
                return False
            
            if x == x2 and y == y2:
                return True
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def handle_input(self) -> bool:
        """Handle player input. Returns False if game should quit."""
        for event in tcod.event.get():
            if event.type == "QUIT":
                return False
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.K_ESCAPE:
                    return False
                elif event.sym == tcod.event.K_UP:
                    self.move_player(0, -1)
                elif event.sym == tcod.event.K_DOWN:
                    self.move_player(0, 1)
                elif event.sym == tcod.event.K_LEFT:
                    self.move_player(-1, 0)
                elif event.sym == tcod.event.K_RIGHT:
                    self.move_player(1, 0)
                elif event.sym == tcod.event.K_PERIOD:
                    # Try to go down stairs
                    if self.dungeon.stairs_pos and (self.player.x, self.player.y) == self.dungeon.stairs_pos:
                        if self.player.current_level < DUNGEON_DEPTH:
                            self.load_level(self.player.current_level + 1)
                        elif self.player.has_amulet:
                            self.state = GameState.GAME_WON
                            self.entering_name = True
                            return True
                        else:
                            self.add_message("You need the Amulet of Yendor first!")
                    else:
                        self.add_message("No stairs here!")

                self.update_game()
                return True

        return True

    def move_player(self, dx: int, dy: int):
        """Move player and handle interactions"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy

        if not self.dungeon.is_walkable(new_x, new_y):
            return

        # Check for monsters
        for monster in self.dungeon.monsters:
            if monster.x == new_x and monster.y == new_y:
                damage = self.player.attack(monster)
                self.add_message(f"Hit {monster.name} for {damage} damage!")
                if monster.health <= 0:
                    self.dungeon.monsters.remove(monster)
                    self.add_message(f"{monster.name} died!")
                return

        # Move player
        self.player.move(dx, dy)

        # Check for items
        items_to_remove = []
        for item in self.dungeon.items:
            if item.x == self.player.x and item.y == self.player.y:
                msg = item.pick_up(self.player)
                self.add_message(msg)
                items_to_remove.append(item)

        for item in items_to_remove:
            self.dungeon.items.remove(item)

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
            self.entering_name = True

    def render(self):
        """Render the game to the console"""
        self.console.clear()

        # Compute FOV
        self.compute_fov()

        # Draw map
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.visible[y, x]:
                    if self.dungeon.tiles[y][x].value == 0:  # Wall
                        self.console.print(x, y, '#', (100, 100, 100))
                    else:  # Floor
                        self.console.print(x, y, '.', (150, 150, 150))
                elif self.explored[y, x]:
                    if self.dungeon.tiles[y][x].value == 0:  # Wall
                        self.console.print(x, y, '#', (50, 50, 50))
                    else:  # Floor
                        self.console.print(x, y, '.', (80, 80, 80))

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

        if self.entering_name:
            # Show name entry screen
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 - 2, "Enter your name:", (255, 255, 255))
            self.console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2, self.input_buffer + "_", (200, 255, 200))
            self.console.print(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 + 2,
                             "Press Enter to confirm", (200, 200, 200))
        elif self.state == GameState.PLAYER_DEAD:
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2, "YOU DIED!", (255, 0, 0))
            self.console.print(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 + 2,
                             "Press R to restart or Q to quit", (200, 200, 200))
        elif self.state == GameState.GAME_WON:
            self.console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2, "YOU WON!", (0, 255, 0))
            self.console.print(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 + 2,
                             "Press R to restart or Q to quit", (200, 200, 200))

        self.context.present(self.console)

    def game_over_input(self) -> bool:
        """Handle input when game is over"""
        for event in tcod.event.get():
            if event.type == "QUIT":
                return False
            elif event.type == "KEYDOWN":
                if self.entering_name:
                    # Handle name input
                    if event.sym == tcod.event.K_RETURN:
                        if self.input_buffer.strip():
                            self.save_score()
                            self.entering_name = False
                            return True
                    elif event.sym == tcod.event.K_BACKSPACE:
                        self.input_buffer = self.input_buffer[:-1]
                    elif event.sym == tcod.event.K_ESCAPE:
                        # Skip entering name
                        self.save_score()
                        self.entering_name = False
                        return True
                    elif hasattr(event, 'text') and len(self.input_buffer) < 20:
                        if event.text and event.text.isprintable():
                            self.input_buffer += event.text
                else:
                    # Handle game over input
                    if event.sym == tcod.event.K_r:
                        self.new_game()
                        return True
                    elif event.sym == tcod.event.K_q or event.sym == tcod.event.K_ESCAPE:
                        return False
        return True

    def save_score(self):
        """Save the current score to the leaderboard"""
        player_name = self.input_buffer.strip() or "Anonymous"
        outcome = "won" if self.state == GameState.GAME_WON else "died"
        
        self.leaderboard.add_entry(
            player_name=player_name,
            gold=self.player.gold,
            level=self.player.current_level,
            outcome=outcome,
            death_cause=self.death_cause
        )

    def run(self):
        """Main game loop"""
        with tcod.context.new(
            columns=SCREEN_WIDTH,
            rows=SCREEN_HEIGHT,
            title="Roguelike Dungeon",
            vsync=True,
        ) as self.context:
            self.new_game()

            while True:
                self.render()

                if self.state == GameState.PLAYING:
                    if not self.handle_input():
                        break
                else:
                    if not self.game_over_input():
                        break
