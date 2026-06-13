"""
Base entity classes (Actor, Player, Item)
"""

import random
from typing import Tuple


class Item:
    """Base class for items"""
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.x = x
        self.y = y

    def pick_up(self, player: 'Player'):
        raise NotImplementedError


class Actor:
    """Base class for player and monsters"""
    def __init__(self, name: str, x: int, y: int, char: str, color: Tuple[int, int, int],
                 health: int, strength: int):
        self.name = name
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.max_health = health
        self.health = health
        self.strength = strength

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def take_damage(self, damage: int):
        self.health -= damage

    def attack(self, target: 'Actor'):
        """Return damage dealt"""
        damage = max(1, self.strength + random.randint(-2, 2))
        target.take_damage(damage)
        return damage


class Player(Actor):
    """The player character"""
    def __init__(self, x: int, y: int):
        super().__init__("Player", x, y, '@', (255, 255, 255), health=100, strength=10)
        self.gold = 0
        self.strength_bonus = 0  # Permanent strength increase from weapons
        self.status_effects = {}  # {stat: [(amount, turns_remaining), ...]}
        self.current_level = 1
        self.has_amulet = False

    def get_total_stat(self, stat: str) -> int:
        """Get stat including temporary effects"""
        if stat == "strength":
            base = self.strength + self.strength_bonus
        elif stat == "health":
            base = self.health
        else:
            return 0

        if stat in self.status_effects:
            for amount, _ in self.status_effects[stat]:
                base += amount

        return base

    def add_status_effect(self, stat: str, amount: int, duration: int):
        """Add a temporary status effect"""
        if stat not in self.status_effects:
            self.status_effects[stat] = []
        self.status_effects[stat].append([amount, duration])

    def update_status_effects(self):
        """Decrease duration of status effects"""
        for stat in self.status_effects:
            self.status_effects[stat] = [[amount, turns - 1]
                                        for amount, turns in self.status_effects[stat]
                                        if turns > 1]

    @property
    def current_strength(self) -> int:
        return self.get_total_stat("strength")
