"""
Monster definitions - Easy to modify and extend
"""

from entities import Actor


class Monster(Actor):
    """Base class for monsters"""
    def __init__(self, name: str, x: int, y: int, char: str, color: tuple,
                 health: int, strength: int):
        super().__init__(name, x, y, char, color, health, strength)


class Falcon(Monster):
    """A predatory bird"""
    def __init__(self, x: int, y: int):
        super().__init__("Falcon", x, y, 'f', (150, 100, 255), health=10, strength=5)


class Emu(Monster):
    """A large flightless bird"""
    def __init__(self, x: int, y: int):
        super().__init__("Emu", x, y, 'e', (100, 100, 100), health=15, strength=7)
