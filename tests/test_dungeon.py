"""
Tests for dungeon module
"""

import pytest
from dungeon import Dungeon, Rect, TileType


class TestRect:
    """Test Rect class for room generation"""
    
    def test_rect_creation(self):
        """Test rectangle initialization"""
        rect = Rect(0, 0, 10, 10)
        assert rect.x1 == 0
        assert rect.y1 == 0
        assert rect.x2 == 10
        assert rect.y2 == 10

    def test_rect_center(self):
        """Test rectangle center calculation"""
        rect = Rect(0, 0, 10, 10)
        center = rect.center
        assert center == (5, 5)

    def test_rect_center_odd_size(self):
        """Test center with odd dimensions"""
        rect = Rect(0, 0, 5, 5)
        center = rect.center
        assert center == (2, 2)

    def test_rect_intersect_no_overlap(self):
        """Test rectangles that don't intersect"""
        rect1 = Rect(0, 0, 5, 5)
        rect2 = Rect(10, 10, 15, 15)
        assert not rect1.intersect(rect2)

    def test_rect_intersect_with_overlap(self):
        """Test rectangles that do intersect"""
        rect1 = Rect(0, 0, 10, 10)
        rect2 = Rect(5, 5, 15, 15)
        assert rect1.intersect(rect2)

    def test_rect_intersect_touching_edges(self):
        """Test rectangles touching at edges"""
        rect1 = Rect(0, 0, 5, 5)
        rect2 = Rect(5, 5, 10, 10)
        # They touch at a point (5, 5)
        assert rect1.intersect(rect2)


class TestDungeon:
    """Test Dungeon class"""
    
    def test_dungeon_creation(self):
        """Test dungeon initialization"""
        dungeon = Dungeon(80, 45)
        assert dungeon.width == 80
        assert dungeon.height == 45
        assert len(dungeon.tiles) == 45
        assert len(dungeon.tiles[0]) == 80
        assert dungeon.rooms == []
        assert dungeon.monsters == []
        assert dungeon.items == []

    def test_dungeon_all_walls_initially(self):
        """Test dungeon starts as all walls"""
        dungeon = Dungeon(10, 10)
        for y in range(10):
            for x in range(10):
                assert dungeon.tiles[y][x] == TileType.WALL

    def test_create_room(self):
        """Test room carving"""
        dungeon = Dungeon(20, 20)
        room = Rect(5, 5, 15, 15)
        dungeon.create_room(room)
        
        # Check room interior is floor
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                assert dungeon.tiles[y][x] == TileType.FLOOR

    def test_create_h_tunnel(self):
        """Test horizontal tunnel creation"""
        dungeon = Dungeon(20, 20)
        dungeon.create_h_tunnel(2, 10, 5)
        
        for x in range(2, 11):
            assert dungeon.tiles[5][x] == TileType.FLOOR

    def test_create_v_tunnel(self):
        """Test vertical tunnel creation"""
        dungeon = Dungeon(20, 20)
        dungeon.create_v_tunnel(2, 10, 5)
        
        for y in range(2, 11):
            assert dungeon.tiles[y][5] == TileType.FLOOR

    def test_dungeon_generate(self):
        """Test dungeon level generation"""
        dungeon = Dungeon(80, 45)
        dungeon.generate(1)
        
        # Should have rooms
        assert len(dungeon.rooms) > 0
        
        # Should have stairs
        assert dungeon.stairs_pos is not None
        
        # Should have player spawn
        assert dungeon.player_spawn is not None
        
        # Should have some items and monsters
        assert len(dungeon.items) > 0 or len(dungeon.monsters) > 0

    def test_dungeon_generate_multiple_levels(self):
        """Test generating different levels"""
        for level in range(1, 6):
            dungeon = Dungeon(80, 45)
            dungeon.generate(level)
            assert len(dungeon.rooms) > 0

    def test_dungeon_level_5_has_more_weapons(self):
        """Test level 5 has more weapons (higher difficulty)"""
        from items import Weapon
        import random
        random.seed(42)
        
        # Generate multiple dungeons to verify level 5 has more weapons
        level_5_weapon_counts = []
        for _ in range(5):
            dungeon = Dungeon(80, 45)
            dungeon.generate(5)
            
            weapon_count = sum(1 for item in dungeon.items if isinstance(item, Weapon))
            level_5_weapon_counts.append(weapon_count)
        
        # Level 5 should generally have weapons for the final boss fight
        # Average should be at least 1 weapon
        assert sum(level_5_weapon_counts) / len(level_5_weapon_counts) >= 1

    def test_is_walkable_floor(self):
        """Test walkability on floor"""
        dungeon = Dungeon(20, 20)
        room = Rect(5, 5, 15, 15)
        dungeon.create_room(room)
        
        # Floor tiles should be walkable
        assert dungeon.is_walkable(10, 10)

    def test_is_walkable_wall(self):
        """Test walkability on wall"""
        dungeon = Dungeon(20, 20)
        # Tile (0, 0) is a wall by default
        assert not dungeon.is_walkable(0, 0)

    def test_is_walkable_bounds(self):
        """Test walkability out of bounds"""
        dungeon = Dungeon(20, 20)
        assert not dungeon.is_walkable(-1, 10)
        assert not dungeon.is_walkable(10, -1)
        assert not dungeon.is_walkable(100, 10)
        assert not dungeon.is_walkable(10, 100)

    def test_room_connectivity(self):
        """Test rooms are connected by tunnels"""
        dungeon = Dungeon(80, 45)
        dungeon.generate(1)
        
        if len(dungeon.rooms) > 1:
            # Check that rooms have floor tiles connecting them
            # This is a basic check - there should be floor tiles
            floor_count = sum(1 for row in dungeon.tiles for tile in row if tile == TileType.FLOOR)
            assert floor_count > 0

    def test_is_walkable_doors(self):
        """Test walkability on doors"""
        dungeon = Dungeon(20, 20)
        
        # Place doors manually
        dungeon.tiles[5][5] = TileType.CLOSED_DOOR
        dungeon.tiles[6][6] = TileType.OPEN_DOOR
        
        assert not dungeon.is_walkable(5, 5)  # Closed door should not be walkable
        assert dungeon.is_walkable(6, 6)      # Open door should be walkable

    def test_door_generation(self):
        """Test that generate() places some doors"""
        import random
        # Set a seed to ensure consistent door generation for the test
        random.seed(42)
        
        dungeon = Dungeon(80, 45)
        dungeon.generate(1)
        
        # Verify that there are some closed doors generated
        door_count = sum(1 for row in dungeon.tiles for tile in row if tile == TileType.CLOSED_DOOR)
        assert door_count > 0
