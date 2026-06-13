"""
Tests for the Game class and tileset loading/generation
"""

import os
import pathlib
import pytest
import tcod
from PIL import Image

from game import Game, GameState
from create_tileset import create_tileset
from leaderboard import LEADERBOARD_FILE


@pytest.fixture(autouse=True)
def clean_leaderboard():
    """Ensure leaderboard.json does not exist before and after tests"""
    if LEADERBOARD_FILE.exists():
        LEADERBOARD_FILE.unlink()
    yield
    if LEADERBOARD_FILE.exists():
        LEADERBOARD_FILE.unlink()


def test_create_tileset(tmp_path):
    """Test that create_tileset successfully creates a tileset image with correct size"""
    filename = tmp_path / "test_tileset.png"
    result = create_tileset(filename=str(filename), tile_size=16)
    
    assert os.path.exists(result)
    assert result == str(filename)
    
    # Open image and verify dimensions
    with Image.open(result) as img:
        # 32 columns * 16 width = 512, 8 rows * 16 height = 128
        assert img.size == (512, 128)
        assert img.mode == "RGB"


def test_game_initialization():
    """Test Game state after init"""
    game = Game()
    assert game.context is None
    assert game.player is not None
    assert game.dungeon is None
    assert game.state == GameState.PLAYING
    assert game.visible is None
    assert game.explored is None
    assert len(game.message_log) == 0
    assert game.turn_count == 0
    assert game.death_cause is None
    assert game.input_buffer == ""
    assert not game.entering_name


def test_game_new_game():
    """Test starting a new game"""
    game = Game()
    # Mock load_level since we don't want to generate full dungeon or we can just let it run
    game.new_game()
    
    assert game.player.current_level == 1
    assert not game.player.has_amulet
    assert game.state == GameState.PLAYING
    assert game.turn_count == 0
    assert "Welcome to the Roguelike Dungeon!" in game.message_log
    assert game.dungeon is not None
    assert game.visible is not None
    assert game.explored is not None


def test_game_add_message():
    """Test message log size limits"""
    game = Game()
    game.add_message("Msg 1")
    game.add_message("Msg 2")
    game.add_message("Msg 3")
    assert len(game.message_log) == 3
    
    game.add_message("Msg 4")
    assert len(game.message_log) == 3
    assert game.message_log == ["Msg 2", "Msg 3", "Msg 4"]


def test_load_tileset_file_exists(tmp_path, monkeypatch):
    """Test load_tileset when the tileset file exists"""
    # Create a dummy tileset in the tmp_path
    tileset_file = tmp_path / "deja10x10_gs_tc.png"
    create_tileset(filename=str(tileset_file), tile_size=16)
    
    # Use monkeypatch to make pathlib.Path(__file__).parent resolve to tmp_path
    # inside load_tileset method.
    class MockPath:
        def __init__(self, *args):
            pass
        @property
        def parent(self):
            return tmp_path
            
    monkeypatch.setattr(pathlib, "Path", MockPath)
    
    game = Game()
    tileset = game.load_tileset()
    
    assert tileset is not None
    assert isinstance(tileset, tcod.tileset.Tileset)


def test_load_tileset_file_missing(tmp_path, monkeypatch):
    """Test load_tileset when the tileset file does not exist"""
    # Empty directory
    class MockPath:
        def __init__(self, *args):
            pass
        @property
        def parent(self):
            return tmp_path
            
    monkeypatch.setattr(pathlib, "Path", MockPath)
    
    game = Game()
    tileset = game.load_tileset()
    assert tileset is None


def test_load_real_tileset():
    """Test load_tileset with the actual deja10x10_gs_tc.png file in the repository"""
    game = Game()
    # Ensure the real file actually exists in parent folder, which it does in our workspace
    tileset = game.load_tileset()
    assert tileset is not None
    assert isinstance(tileset, tcod.tileset.Tileset)


def test_game_over_input_text_input(monkeypatch):
    """Test that game_over_input correctly appends characters from TextInput events"""
    game = Game()
    game.entering_name = True
    game.input_buffer = "Alice"
    
    # Mock tcod.event.get() to return a TextInput event
    mock_events = [tcod.event.TextInput(text="b")]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    
    res = game.game_over_input()
    assert res is True
    assert game.input_buffer == "Aliceb"


def test_game_over_input_backspace(monkeypatch):
    """Test that game_over_input handles Backspace key to remove last character"""
    game = Game()
    game.entering_name = True
    game.input_buffer = "Alice"
    
    # Mock tcod.event.get() to return a KeyDown event with K_BACKSPACE
    mock_events = [tcod.event.KeyDown(sym=tcod.event.K_BACKSPACE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    
    res = game.game_over_input()
    assert res is True
    assert game.input_buffer == "Alic"


def test_game_over_input_return(monkeypatch):
    """Test that game_over_input handles Return key to save score and exit name entry"""
    game = Game()
    game.entering_name = True
    game.input_buffer = "Alice"
    
    # Mock leaderboard.add_entry
    saved_entries = []
    monkeypatch.setattr(game.leaderboard, "add_entry", lambda **kwargs: saved_entries.append(kwargs))
    
    mock_events = [tcod.event.KeyDown(sym=tcod.event.K_RETURN, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    
    res = game.game_over_input()
    assert res is True
    assert not game.entering_name
    assert len(saved_entries) == 1
    assert saved_entries[0]["player_name"] == "Alice"


