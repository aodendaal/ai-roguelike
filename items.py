"""
Item definitions - Easy to modify and extend
"""

from entities import Item


class Gold(Item):
    """Gold currency"""
    def __init__(self, x: int, y: int, amount: int = 10):
        super().__init__("Gold", x, y)
        self.amount = amount
        self.char = '$'
        self.color = (255, 255, 0)

    def pick_up(self, player):
        player.gold += self.amount
        return f"Gained {self.amount} gold!"


class Potion(Item):
    """Potion that temporarily modifies stats"""
    def __init__(self, x: int, y: int, stat: str, amount: int, duration: int):
        super().__init__(f"Potion of {stat}", x, y)
        self.stat = stat  # "strength" or "health"
        self.amount = amount
        self.duration = duration
        self.char = '!'
        self.color = (255, 100, 100) if amount > 0 else (100, 100, 255)
        self.color_name = "unknown"

    def get_description(self) -> str:
        return f"a {self.color_name} potion"

    def pick_up(self, player):
        player.inventory.append(self)
        return f"Picked up {self.get_description()}."

    def quaff(self, player) -> str:
        if self.stat == "health":
            if self.amount > 0:
                player.health = min(player.max_health, player.health + self.amount)
                return f"Drank potion: gain {self.amount} health"
            else:
                player.health = player.health + self.amount
                return f"Drank potion: lose {abs(self.amount)} health"
        else:
            player.add_status_effect(self.stat, self.amount, self.duration)
            sign = "+" if self.amount > 0 else ""
            return f"Drank potion: {sign}{self.amount} {self.stat} for {self.duration} turns!"


class Weapon(Item):
    """Weapon that permanently increases strength"""
    def __init__(self, x: int, y: int, strength_bonus: int, name: str = "Sword"):
        super().__init__(name, x, y)
        self.strength_bonus = strength_bonus
        self.char = ')'
        self.color = (200, 200, 100)

    def pick_up(self, player):
        player.strength_bonus += self.strength_bonus
        return f"Gained {self.name}! +{self.strength_bonus} Strength"


class AmuletOfYendor(Item):
    """The winning item"""
    def __init__(self, x: int, y: int):
        super().__init__("Amulet of Yendor", x, y)
        self.char = '*'
        self.color = (255, 200, 0)

    def pick_up(self, player):
        player.has_amulet = True
        return "You obtained the Amulet of Yendor! Head to the stairs to escape!"
