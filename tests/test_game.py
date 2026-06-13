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
from dungeon import Dungeon


@pytest.fixture(autouse=True)
def clean_test_artifacts():
    """Ensure leaderboard.json and scaled tilesets do not exist before and after tests"""
    if LEADERBOARD_FILE.exists():
        LEADERBOARD_FILE.unlink()
    scaled_file = pathlib.Path(__file__).parent.parent / "deja10x10_gs_tc_scaled.png"
    if scaled_file.exists():
        scaled_file.unlink()
    yield
    if LEADERBOARD_FILE.exists():
        LEADERBOARD_FILE.unlink()
    if scaled_file.exists():
        scaled_file.unlink()


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
    assert game.state == GameState.MENU
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
    
    # Mock tcod.event.get() to return a KeyDown event with KeySym.BACKSPACE
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.BACKSPACE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    
    res = game.game_over_input()
    assert res is True
    assert game.input_buffer == "Alic"


def test_game_over_input_return(monkeypatch):
    """Test that game_over_input handles Return key to start the game and save name"""
    game = Game()
    game.entering_name = True
    game.input_buffer = "Alice"
    
    # Mock leaderboard.add_entry (should not be called yet)
    saved_entries = []
    monkeypatch.setattr(game.leaderboard, "add_entry", lambda **kwargs: saved_entries.append(kwargs))
    
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    
    res = game.game_over_input()
    assert res is True
    assert not game.entering_name
    assert game.state == GameState.PLAYING
    assert game.player_name == "Alice"
    assert len(saved_entries) == 0


def test_entering_name_toggles_text_input():
    """Test that setting entering_name property calls start/stop_text_input on context.sdl_window"""
    game = Game()
    
    # Create a mock sdl_window
    class MockSDLWindow:
        def __init__(self):
            self.start_called = 0
            self.stop_called = 0
        def start_text_input(self):
            self.start_called += 1
        def stop_text_input(self):
            self.stop_called += 1
            
    class MockContext:
        def __init__(self):
            self.sdl_window = MockSDLWindow()
            
    mock_ctx = MockContext()
    game.context = mock_ctx
    
    # Transition to True
    game.entering_name = True
    assert mock_ctx.sdl_window.start_called == 1
    assert mock_ctx.sdl_window.stop_called == 0
    
    # Transition to False
    game.entering_name = False
    assert mock_ctx.sdl_window.start_called == 1
    assert mock_ctx.sdl_window.stop_called == 1


def test_game_menu_navigation(monkeypatch):
    """Test that main menu keys transition to correct states"""
    game = Game()
    assert game.state == GameState.MENU
    
    # Pressing 1 transitions to ENTERING_NAME
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.N1, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    res = game.process_events()
    assert res is True
    assert game.state == GameState.ENTERING_NAME
    
    # Pressing Escape in ENTERING_NAME transitions back to MENU
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    res = game.process_events()
    assert res is True
    assert game.state == GameState.MENU
    
    # Pressing 2 transitions to VIEW_LEADERBOARD
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.N2, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    res = game.process_events()
    assert res is True
    assert game.state == GameState.VIEW_LEADERBOARD
    
    # Pressing Space in VIEW_LEADERBOARD transitions back to MENU
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.SPACE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    res = game.process_events()
    assert res is True
    assert game.state == GameState.MENU


def test_player_death_saves_score(monkeypatch):
    """Test that player death automatically saves score and transitions to PLAYER_DEAD"""
    game = Game()
    game.player_name = "Bob"
    game.state = GameState.PLAYING
    
    import numpy as np
    from constants import MAP_WIDTH, MAP_HEIGHT
    game.visible = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
    game.explored = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
    
    # Mock dungeon so we can update game
    game.dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT)
    game.player.health = 10
    
    saved_entries = []
    monkeypatch.setattr(game.leaderboard, "add_entry", lambda **kwargs: saved_entries.append(kwargs))
    
    # Kill the player
    game.player.health = 0
    game.update_game()
    
    assert game.state == GameState.PLAYER_DEAD
    assert len(saved_entries) == 1
    assert saved_entries[0]["player_name"] == "Bob"
    assert saved_entries[0]["outcome"] == "died"


def test_player_opens_door():
    """Test that a player moving into a CLOSED_DOOR opens it"""
    from dungeon import TileType
    from constants import MAP_WIDTH, MAP_HEIGHT
    
    game = Game()
    game.state = GameState.PLAYING
    game.dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT)
    
    # Initialize visible/explored arrays
    import numpy as np
    game.visible = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
    game.explored = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
    
    # Set player position
    game.player.x, game.player.y = 5, 5
    
    # Put a closed door to the right of the player
    game.dungeon.tiles[5][6] = TileType.CLOSED_DOOR
    
    # Try to move player right
    game.move_player(1, 0)
    
    # Verify player did not move (still at (5, 5))
    assert game.player.x == 5
    assert game.player.y == 5
    
    # Verify the door is now open
    assert game.dungeon.tiles[5][6] == TileType.OPEN_DOOR
    
    # Verify message was logged
    assert "You open the door." in game.message_log


def test_fov_sees_non_walkable_tiles():
    """Test that player FOV sees walls and closed doors, but not beyond them"""
    from dungeon import TileType
    from constants import MAP_WIDTH, MAP_HEIGHT
    
    game = Game()
    game.state = GameState.PLAYING
    game.dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT)
    
    # Initialize visible/explored arrays
    import numpy as np
    game.visible = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
    game.explored = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
    
    # Set player at (5, 5)
    game.player.x, game.player.y = 5, 5
    
    # Fill background with walkable floor
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            game.dungeon.tiles[y][x] = TileType.FLOOR
            
    # Put a closed door at (5, 7) and a wall at (5, 8)
    game.dungeon.tiles[5][7] = TileType.CLOSED_DOOR
    game.dungeon.tiles[5][8] = TileType.WALL
    
    # Compute FOV
    game.compute_fov()
    
    # The floor right next to the player (5, 6) should be visible
    assert game.visible[5, 6]
    
    # The closed door at (5, 7) should be visible
    assert game.visible[5, 7]
    
    # The wall at (5, 8) should NOT be visible because the closed door at (5, 7) blocked the line of sight
    assert not game.visible[5, 8]


def test_floor_pastel_colors():
    """Test that floor pastel colors are fetched correctly for each level and fallback properly"""
    game = Game()
    
    # Test level 1 (Soft Lavender/Purple)
    game.player.current_level = 1
    colors_1 = game.get_floor_colors()
    assert colors_1["wall_visible"] == (150, 140, 180)
    assert colors_1["floor_visible"] == (200, 190, 220)
    
    # Test level 2 (Soft Mint/Green)
    game.player.current_level = 2
    colors_2 = game.get_floor_colors()
    assert colors_2["wall_visible"] == (130, 170, 140)
    
    # Test level 5 (Soft Rose/Pink)
    game.player.current_level = 5
    colors_5 = game.get_floor_colors()
    assert colors_5["wall_visible"] == (180, 135, 150)
    
    # Test fallback wrapping (level 6 should wrap to level 1)
    game.player.current_level = 6
    colors_6 = game.get_floor_colors()
    assert colors_6["wall_visible"] == (150, 140, 180)


def test_character_life_status_screen():
    """Test that all stats are correctly tracked and reset"""
    from dungeon import TileType
    from items import Potion, Weapon
    from monsters import Falcon
    
    game = Game()
    game.new_game()
    
    # Verify initial stats are 0
    assert game.potions_drunk == 0
    assert game.weapons_picked_up == 0
    assert game.doors_opened == 0
    assert game.monsters_killed == 0
    assert game.floors_descended == 0
    
    # 1. Test door opened stat
    game.dungeon.tiles[5][6] = TileType.CLOSED_DOOR
    game.player.x, game.player.y = 5, 5
    game.move_player(1, 0)
    assert game.doors_opened == 1
    
    # 2. Test monsters killed stat
    # Ensure tiles are floors so the player doesn't hit a wall check
    game.dungeon.tiles[5][5] = TileType.FLOOR
    game.dungeon.tiles[6][5] = TileType.FLOOR
    monster = Falcon(5, 6)
    monster.health = 1  # make it easy to kill
    game.dungeon.monsters = [monster]
    game.move_player(0, 1)  # moves into Falcon
    assert game.monsters_killed == 1
    
    # 3. Test item pickup stats (potions & weapons)
    potion = Potion(5, 5, "strength", 2, 10)
    weapon = Weapon(5, 5, 1)
    game.dungeon.items = [potion, weapon]
    # Stand player at (5, 5) and run move_player with no movement to trigger pickup of auto-pickup weapon
    game.move_player(0, 0)
    assert game.weapons_picked_up == 1
    # Potion should still be on the ground
    assert potion in game.dungeon.items
    
    # Pick up the potion manually
    game.pickup_item()
    assert potion not in game.dungeon.items
    assert len(game.player.inventory) == 1
    assert game.player.inventory[0] == potion
    
    # Quaff the potion
    mock_quaff_events = [
        tcod.event.KeyDown(sym=tcod.event.KeySym.Q, scancode=0, mod=0, repeat=False),
        tcod.event.KeyDown(sym=tcod.event.KeySym.A, scancode=0, mod=0, repeat=False)
    ]
    from unittest.mock import patch
    with patch("tcod.event.get", return_value=mock_quaff_events):
        game.process_events()
    assert game.potions_drunk == 1
    assert len(game.player.inventory) == 0
    
    # 4. Test floors descended stat
    game.dungeon.stairs_pos = (5, 5)
    
    # Mock game.process_events event loop
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.PERIOD, scancode=0, mod=0, repeat=False)]
    import pytest
    from unittest.mock import patch
    with patch("tcod.event.get", return_value=mock_events):
        game.process_events()
    
    assert game.floors_descended == 1


def test_inventory_and_quaff_menus(monkeypatch):
    """Test inventory and quaff menu interactions via key events"""
    game = Game()
    game.new_game()
    game.state = GameState.PLAYING
    
    # 1. Test opening inventory menu
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.I, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.INVENTORY
    
    # 2. Test closing inventory menu with 'i'
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.I, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.PLAYING
    
    # 3. Test opening inventory and closing with Escape
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.I, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.INVENTORY
    
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.PLAYING
    
    # 4. Test opening quaff menu and closing with Escape
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.Q, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.QUAFF_MENU
    
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.PLAYING
    
    # 5. Test trying to quaff with an empty inventory
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.Q, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.QUAFF_MENU
    
    # Press 'a' (index 0) which is empty/invalid
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.A, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    # State should remain in QUAFF_MENU because selection was invalid
    assert game.state == GameState.QUAFF_MENU
    
    # 6. Press Escape to clear
    mock_events = [tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, scancode=0, mod=0, repeat=False)]
    monkeypatch.setattr(tcod.event, "get", lambda: mock_events)
    game.process_events()
    assert game.state == GameState.PLAYING

    # 7. Test pickup when nothing is on floor
    game.dungeon.items = []
    game.pickup_item()
    assert "nothing here" in game.message_log[-1].lower()

    # 8. Test stepping over a potion shows a message
    from items import Potion
    potion = Potion(game.player.x + 1, game.player.y, "strength", 3, 5)
    potion.color_name = "blue"
    game.dungeon.items = [potion]
    game.move_player(1, 0)
    assert "you see a blue potion here" in game.message_log[-1].lower()



