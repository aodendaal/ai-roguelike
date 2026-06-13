"""
Tests for items module
"""

import pytest
from entities import Player
from items import Gold, Potion, Weapon, AmuletOfYendor


class TestGold:
    """Test Gold item"""
    
    def test_gold_creation(self):
        """Test gold initialization"""
        gold = Gold(5, 10, 25)
        assert gold.x == 5
        assert gold.y == 10
        assert gold.amount == 25
        assert gold.char == '$'
        assert gold.name == "Gold"

    def test_gold_pickup(self):
        """Test picking up gold"""
        player = Player(0, 0)
        gold = Gold(0, 0, 50)
        msg = gold.pick_up(player)
        
        assert player.gold == 50
        assert "50" in msg
        assert "gold" in msg.lower()


class TestPotion:
    """Test Potion item"""
    
    def test_potion_creation(self):
        """Test potion initialization"""
        potion = Potion(5, 10, "strength", 5, 3)
        assert potion.x == 5
        assert potion.y == 10
        assert potion.stat == "strength"
        assert potion.amount == 5
        assert potion.duration == 3
        assert potion.char == '!'

    def test_potion_positive_effect(self):
        """Test positive potion effect"""
        potion = Potion(0, 0, "strength", 5, 3)
        assert potion.color == (255, 100, 100)

    def test_potion_negative_effect(self):
        """Test negative potion effect"""
        potion = Potion(0, 0, "health", -3, 2)
        assert potion.color == (100, 100, 255)

    def test_potion_pickup(self):
        """Test picking up a potion"""
        player = Player(0, 0)
        potion = Potion(0, 0, "strength", 5, 3)
        msg = potion.pick_up(player)
        
        assert "strength" in msg.lower()
        assert "+5" in msg
        assert "3" in msg
        assert player.current_strength == 15  # 10 + 5 from potion


class TestWeapon:
    """Test Weapon item"""
    
    def test_weapon_creation(self):
        """Test weapon initialization"""
        weapon = Weapon(5, 10, 3, "Sword")
        assert weapon.x == 5
        assert weapon.y == 10
        assert weapon.strength_bonus == 3
        assert weapon.name == "Sword"
        assert weapon.char == '/'
        assert weapon.color == (200, 200, 100)

    def test_weapon_default_name(self):
        """Test weapon default name"""
        weapon = Weapon(0, 0, 2)
        assert weapon.name == "Sword"

    def test_weapon_pickup(self):
        """Test picking up a weapon"""
        player = Player(0, 0)
        weapon = Weapon(0, 0, 5, "Excalibur")
        msg = weapon.pick_up(player)
        
        assert player.strength_bonus == 5
        assert player.current_strength == 15  # 10 + 5
        assert "Excalibur" in msg
        assert "+5" in msg

    def test_multiple_weapons(self):
        """Test picking up multiple weapons"""
        player = Player(0, 0)
        weapon1 = Weapon(0, 0, 3, "Sword")
        weapon2 = Weapon(1, 1, 2, "Dagger")
        
        weapon1.pick_up(player)
        weapon2.pick_up(player)
        
        assert player.strength_bonus == 5
        assert player.current_strength == 15


class TestAmuletOfYendor:
    """Test Amulet of Yendor"""
    
    def test_amulet_creation(self):
        """Test amulet initialization"""
        amulet = AmuletOfYendor(5, 10)
        assert amulet.x == 5
        assert amulet.y == 10
        assert amulet.name == "Amulet of Yendor"
        assert amulet.char == '*'
        assert amulet.color == (255, 200, 0)

    def test_amulet_pickup(self):
        """Test picking up the amulet"""
        player = Player(0, 0)
        amulet = AmuletOfYendor(0, 0)
        msg = amulet.pick_up(player)
        
        assert player.has_amulet is True
        assert "Amulet" in msg
        assert "Yendor" in msg
