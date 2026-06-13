"""
Tests for entities module
"""

import pytest
from entities import Player, Actor


class TestPlayer:
    """Test Player class"""
    
    def test_player_creation(self):
        """Test player initialization"""
        player = Player(5, 10)
        assert player.x == 5
        assert player.y == 10
        assert player.health == 100
        assert player.max_health == 100
        assert player.strength == 10
        assert player.gold == 0
        assert player.strength_bonus == 0
        assert player.current_level == 1
        assert player.has_amulet is False

    def test_player_move(self):
        """Test player movement"""
        player = Player(5, 5)
        player.move(1, -1)
        assert player.x == 6
        assert player.y == 4

    def test_player_take_damage(self):
        """Test player takes damage"""
        player = Player(0, 0)
        player.take_damage(30)
        assert player.health == 70

    def test_player_death(self):
        """Test player dies at 0 health"""
        player = Player(0, 0)
        player.take_damage(100)
        assert player.health == 0

    def test_player_strength_bonus(self):
        """Test strength bonus from weapons"""
        player = Player(0, 0)
        player.strength_bonus = 5
        assert player.current_strength == 15  # 10 base + 5 bonus

    def test_add_status_effect(self):
        """Test adding temporary status effects"""
        player = Player(0, 0)
        player.add_status_effect("strength", 5, 3)
        assert "strength" in player.status_effects
        assert len(player.status_effects["strength"]) == 1
        assert player.status_effects["strength"][0] == [5, 3]

    def test_status_effect_total_stat(self):
        """Test stat calculation with status effects"""
        player = Player(0, 0)
        player.add_status_effect("strength", 5, 3)
        assert player.get_total_stat("strength") == 15  # 10 base + 5 bonus

    def test_update_status_effects(self):
        """Test status effect duration decreases"""
        player = Player(0, 0)
        player.add_status_effect("strength", 5, 2)
        player.update_status_effects()
        # Effect still exists but with 1 turn left
        assert len(player.status_effects["strength"]) == 1
        assert player.status_effects["strength"][0][1] == 1
        
        # Update again - effect should expire
        player.update_status_effects()
        assert len(player.status_effects["strength"]) == 0

    def test_multiple_status_effects(self):
        """Test multiple status effects on same stat"""
        player = Player(0, 0)
        player.add_status_effect("strength", 3, 2)
        player.add_status_effect("strength", 2, 3)
        assert player.get_total_stat("strength") == 15  # 10 + 3 + 2


class TestActor:
    """Test Actor class"""
    
    def test_actor_attack(self):
        """Test actor attack deals damage"""
        attacker = Actor("Attacker", 0, 0, 'a', (255, 0, 0), 20, 10)
        defender = Actor("Defender", 1, 0, 'd', (0, 255, 0), 20, 5)
        
        initial_health = defender.health
        damage = attacker.attack(defender)
        
        assert damage >= 8  # min: 10 - 2
        assert damage <= 12  # max: 10 + 2
        assert defender.health < initial_health
        assert defender.health == initial_health - damage
