"""
Tests for monsters module
"""

import pytest
from monsters import Falcon, Emu


class TestFalcon:
    """Test Falcon monster"""
    
    def test_falcon_creation(self):
        """Test falcon initialization"""
        falcon = Falcon(5, 10)
        assert falcon.x == 5
        assert falcon.y == 10
        assert falcon.name == "Falcon"
        assert falcon.char == 'f'
        assert falcon.color == (150, 100, 255)
        assert falcon.health == 10
        assert falcon.max_health == 10
        assert falcon.strength == 5

    def test_falcon_position_varies(self):
        """Test multiple falcons have different positions"""
        falcon1 = Falcon(0, 0)
        falcon2 = Falcon(5, 5)
        
        assert falcon1.x != falcon2.x
        assert falcon1.y != falcon2.y
        # But stats should be same
        assert falcon1.strength == falcon2.strength


class TestEmu:
    """Test Emu monster"""
    
    def test_emu_creation(self):
        """Test emu initialization"""
        emu = Emu(5, 10)
        assert emu.x == 5
        assert emu.y == 10
        assert emu.name == "Emu"
        assert emu.char == 'e'
        assert emu.color == (100, 100, 100)
        assert emu.health == 15
        assert emu.max_health == 15
        assert emu.strength == 7

    def test_emu_stronger_than_falcon(self):
        """Test emu is stronger than falcon"""
        falcon = Falcon(0, 0)
        emu = Emu(0, 0)
        
        assert emu.health > falcon.health
        assert emu.strength > falcon.strength
