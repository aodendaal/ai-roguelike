#!/usr/bin/env python3
"""
Tileset generator for Roguelike Dungeon
Creates a custom pixel art tileset for use with libtcod
"""

from PIL import Image, ImageDraw, ImageFont
import sys


def create_tileset(filename="roguelike_tileset.png", tile_size=16):
    """Create a custom tileset for libtcod"""
    
    TILE_WIDTH = tile_size
    TILE_HEIGHT = tile_size
    COLS = 32  # Standard libtcod tileset is 32 columns
    ROWS = 8   # and 8 rows (256 characters total)
    
    # Create image with dark background
    img = Image.new('RGB', (TILE_WIDTH * COLS, TILE_HEIGHT * ROWS), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    
    # Try to load a monospace font
    font = None
    font_sizes = [13, 12, 11]
    for size in font_sizes:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", size)
            break
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
        print("Warning: Using default font (custom font not found)")
    
    # Character color mapping
    char_colors = {
        '@': (0, 200, 0),         # Player - bright green
        'f': (200, 100, 255),     # Falcon - magenta
        'e': (150, 150, 150),     # Emu - gray
        '$': (255, 255, 0),       # Gold - yellow
        '!': (255, 100, 200),     # Potion - pink
        '/': (200, 180, 100),     # Weapon - brown/gold
        '*': (255, 215, 0),       # Amulet - gold
        '>': (200, 200, 200),     # Stairs - light gray
        '<': (200, 200, 200),     # Up stairs - light gray
        '#': (100, 100, 100),     # Wall - dark gray
        '.': (150, 150, 150),     # Floor - medium gray
    }
    
    # Draw all 256 ASCII characters
    for i in range(256):
        char = chr(i)
        col = i % COLS
        row = i // COLS
        x = col * TILE_WIDTH
        y = row * TILE_HEIGHT
        
        # Get color for this character
        color = char_colors.get(char, (150, 150, 150))
        
        # Draw background with subtle grid
        draw.rectangle([x, y, x + TILE_WIDTH - 1, y + TILE_HEIGHT - 1], 
                       fill=(20, 20, 20), outline=(40, 40, 40))
        
        # Draw character with shadow effect for better visibility
        try:
            # Shadow
            draw.text((x + 2, y + 2), char, font=font, fill=(0, 0, 0))
            # Main character
            draw.text((x + 1, y + 1), char, font=font, fill=color)
        except Exception as e:
            print(f"Warning: Could not draw character {repr(char)}: {e}")
    
    # Save the tileset
    img.save(filename)
    print(f"✓ Created {filename}")
    print(f"  - 32x8 grid ({COLS * ROWS} characters)")
    print(f"  - {TILE_WIDTH}x{TILE_HEIGHT} pixels per tile")
    print(f"  - Total dimensions: {TILE_WIDTH * COLS}x{TILE_HEIGHT * ROWS} pixels")
    return filename


if __name__ == "__main__":
    # Allow custom output filename
    output_file = sys.argv[1] if len(sys.argv) > 1 else "roguelike_tileset.png"
    tile_size = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    
    print(f"Generating tileset with {tile_size}x{tile_size} pixel tiles...")
    create_tileset(output_file, tile_size)
