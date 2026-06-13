"""
Tests for the leaderboard module
"""

import pytest
import json
from pathlib import Path
from leaderboard import Leaderboard, LeaderboardEntry, LEADERBOARD_FILE


class TestLeaderboardEntry:
    """Tests for LeaderboardEntry class"""
    
    def test_entry_creation(self):
        """Test creating a leaderboard entry"""
        entry = LeaderboardEntry(
            player_name="Hero",
            gold=500,
            level=5,
            outcome="won"
        )
        assert entry.player_name == "Hero"
        assert entry.gold == 500
        assert entry.level == 5
        assert entry.outcome == "won"
        assert entry.death_cause is None
    
    def test_entry_creation_with_death(self):
        """Test creating an entry with death cause"""
        entry = LeaderboardEntry(
            player_name="Novice",
            gold=100,
            level=2,
            outcome="died",
            death_cause="Falcon"
        )
        assert entry.death_cause == "Falcon"
        assert entry.outcome == "died"
    
    def test_entry_to_dict(self):
        """Test converting entry to dictionary"""
        entry = LeaderboardEntry(
            player_name="Hero",
            gold=500,
            level=5,
            outcome="won"
        )
        data = entry.to_dict()
        assert data["player_name"] == "Hero"
        assert data["gold"] == 500
        assert data["level"] == 5
        assert data["outcome"] == "won"
    
    def test_entry_from_dict(self):
        """Test creating entry from dictionary"""
        data = {
            "player_name": "Hero",
            "gold": 500,
            "level": 5,
            "outcome": "won",
            "death_cause": None,
            "timestamp": "2024-01-01T12:00:00"
        }
        entry = LeaderboardEntry.from_dict(data)
        assert entry.player_name == "Hero"
        assert entry.gold == 500
    
    def test_entry_string_representation_win(self):
        """Test string representation for win"""
        entry = LeaderboardEntry(
            player_name="Winner",
            gold=1000,
            level=5,
            outcome="won"
        )
        s = str(entry)
        assert "Winner" in s
        assert "1000" in s
        assert "Found Amulet of Yendor" in s
    
    def test_entry_string_representation_death(self):
        """Test string representation for death"""
        entry = LeaderboardEntry(
            player_name="Loser",
            gold=100,
            level=2,
            outcome="died",
            death_cause="Emu"
        )
        s = str(entry)
        assert "Loser" in s
        assert "Emu" in s
        assert "Killed by" in s


class TestLeaderboard:
    """Tests for Leaderboard class"""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up leaderboard file after each test"""
        yield
        if LEADERBOARD_FILE.exists():
            LEADERBOARD_FILE.unlink()
    
    def test_leaderboard_creation(self):
        """Test creating a leaderboard"""
        lb = Leaderboard()
        assert lb.entries == []
    
    def test_add_entry(self):
        """Test adding an entry"""
        lb = Leaderboard()
        lb.add_entry(
            player_name="Hero",
            gold=500,
            level=5,
            outcome="won"
        )
        assert len(lb.entries) == 1
        assert lb.entries[0].player_name == "Hero"
    
    def test_add_multiple_entries(self):
        """Test adding multiple entries"""
        lb = Leaderboard()
        lb.add_entry("Hero1", 500, 5, "won")
        lb.add_entry("Hero2", 400, 4, "died", "Falcon")
        lb.add_entry("Hero3", 600, 5, "won")
        assert len(lb.entries) == 3
    
    def test_entries_sorted_by_outcome_then_gold(self):
        """Test that entries are sorted by outcome (wins first) then gold"""
        lb = Leaderboard()
        lb.add_entry("LowGoldWinner", 100, 5, "won")
        lb.add_entry("HighGoldDier", 1000, 2, "died", "Emu")
        lb.add_entry("HighGoldWinner", 500, 5, "won")
        
        # Wins should come first, sorted by gold descending
        assert lb.entries[0].player_name == "HighGoldWinner"
        assert lb.entries[1].player_name == "LowGoldWinner"
        assert lb.entries[2].player_name == "HighGoldDier"
    
    def test_leaderboard_persistence(self):
        """Test that leaderboard is saved and loaded from file"""
        # Create and add entry
        lb1 = Leaderboard()
        lb1.add_entry("Hero", 500, 5, "won")
        
        # Load in new instance
        lb2 = Leaderboard()
        assert len(lb2.entries) == 1
        assert lb2.entries[0].player_name == "Hero"
    
    def test_get_top_entries(self):
        """Test getting top N entries"""
        lb = Leaderboard()
        for i in range(15):
            lb.add_entry(f"Hero{i}", 100 + i * 10, 3, "died", "Monster")
        
        top_10 = lb.get_top_entries(10)
        assert len(top_10) == 10
    
    def test_get_formatted_leaderboard(self):
        """Test formatted leaderboard output"""
        lb = Leaderboard()
        lb.add_entry("Hero", 500, 5, "won")
        
        formatted = lb.get_formatted_leaderboard()
        assert "Hero" in formatted
        assert "LEADERBOARD" in formatted
    
    def test_get_formatted_leaderboard_empty(self):
        """Test formatted leaderboard when empty"""
        lb = Leaderboard()
        formatted = lb.get_formatted_leaderboard()
        assert "No scores yet!" in formatted
    
    def test_save_and_load(self):
        """Test explicit save and load"""
        lb1 = Leaderboard()
        lb1.add_entry("TestHero", 250, 3, "died", "Falcon")
        
        lb2 = Leaderboard()
        assert any(e.player_name == "TestHero" for e in lb2.entries)
    
    def test_leaderboard_file_format(self):
        """Test that leaderboard is stored as valid JSON"""
        lb = Leaderboard()
        lb.add_entry("TestHero", 300, 4, "won")
        
        # Verify file is valid JSON
        with open(LEADERBOARD_FILE) as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["player_name"] == "TestHero"
