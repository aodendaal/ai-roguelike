"""
Leaderboard management - saves and loads player scores
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


LEADERBOARD_FILE = Path("leaderboard.json")


class LeaderboardEntry:
    """Represents a single leaderboard entry"""
    def __init__(
        self,
        player_name: str,
        gold: int,
        level: int,
        outcome: str,  # "won" or "died"
        death_cause: str = None,  # monster name if died
        timestamp: str = None
    ):
        self.player_name = player_name
        self.gold = gold
        self.level = level
        self.outcome = outcome
        self.death_cause = death_cause
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "player_name": self.player_name,
            "gold": self.gold,
            "level": self.level,
            "outcome": self.outcome,
            "death_cause": self.death_cause,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LeaderboardEntry":
        """Create from dictionary"""
        return LeaderboardEntry(
            player_name=data["player_name"],
            gold=data["gold"],
            level=data["level"],
            outcome=data["outcome"],
            death_cause=data.get("death_cause"),
            timestamp=data.get("timestamp")
        )

    def __str__(self) -> str:
        """Format entry for display"""
        if self.outcome == "won":
            result = f"WON - Found Amulet of Yendor!"
        else:
            result = f"DIED - Killed by {self.death_cause}"
        
        return f"{self.player_name:20} | Level {self.level}/5 | Gold: {self.gold:5} | {result}"


class Leaderboard:
    """Manages the leaderboard"""
    def __init__(self):
        self.entries: List[LeaderboardEntry] = []
        self.load()

    def load(self):
        """Load leaderboard from file"""
        if LEADERBOARD_FILE.exists():
            try:
                with open(LEADERBOARD_FILE, "r") as f:
                    data = json.load(f)
                    self.entries = [LeaderboardEntry.from_dict(entry) for entry in data]
                    # Sort by outcome (wins first) then by gold (highest first)
                    self.entries.sort(
                        key=lambda e: (e.outcome == "died", -e.gold)
                    )
            except Exception as e:
                print(f"Error loading leaderboard: {e}")
                self.entries = []
        else:
            self.entries = []

    def save(self):
        """Save leaderboard to file"""
        try:
            data = [entry.to_dict() for entry in self.entries]
            with open(LEADERBOARD_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")

    def add_entry(
        self,
        player_name: str,
        gold: int,
        level: int,
        outcome: str,
        death_cause: str = None
    ):
        """Add a new entry to the leaderboard"""
        entry = LeaderboardEntry(
            player_name=player_name,
            gold=gold,
            level=level,
            outcome=outcome,
            death_cause=death_cause
        )
        self.entries.append(entry)
        
        # Sort by outcome (wins first) then by gold (highest first)
        self.entries.sort(
            key=lambda e: (e.outcome == "died", -e.gold)
        )
        
        self.save()

    def get_top_entries(self, count: int = 10) -> List[LeaderboardEntry]:
        """Get top N entries"""
        return self.entries[:count]

    def get_formatted_leaderboard(self, count: int = 10) -> str:
        """Get formatted leaderboard for display"""
        if not self.entries:
            return "No scores yet!"
        
        lines = ["=== LEADERBOARD ===", ""]
        for i, entry in enumerate(self.get_top_entries(count), 1):
            lines.append(f"{i:2}. {entry}")
        
        return "\n".join(lines)
