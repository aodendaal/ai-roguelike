# Roguelike Dungeon - A Python libtcod Game

A classic roguelike dungeon crawler built with Python and libtcod.

## Features

- **Player Stats**: Strength and Health
- **Equipment System**:
  - Gold currency
  - Potions (temporary stat modifications)
  - Weapons (permanent Strength increase)
- **Enemies**: Falcons and Emus with simple AI
- **Dungeon Generation**: Procedurally generated levels with rooms and corridors
- **5-Level Dungeon**: Each with increasing difficulty
- **Win Condition**: Collect the Amulet of Yendor on level 5 and reach the stairs
- **Lose Condition**: Health drops to 0 or below
- **Restart/Quit**: Game over prompt allows you to restart or quit

## Requirements

- Python 3.8+
- tcod (libtcod Python binding)

## Project Structure

The code is organized into modular files for easy customization:

- **roguelike.py** - Main entry point
- **game.py** - Core game logic, rendering, and event handling
- **entities.py** - Base classes: `Item`, `Actor`, `Player`
- **items.py** - Item definitions (Gold, Potion, Weapon, AmuletOfYendor) - **Easy to modify!**
- **monsters.py** - Monster definitions (Falcon, Emu) - **Easy to modify!**
- **dungeon.py** - Dungeon generation and level layout
- **constants.py** - Game configuration (screen size, dungeon parameters, etc.)

### Customizing Monsters and Items

You can easily add new monsters and items:

**Add a new monster** (in `monsters.py`):

```python
class Dragon(Monster):
    """A fire-breathing dragon"""
    def __init__(self, x: int, y: int):
        super().__init__("Dragon", x, y, 'D', (255, 100, 0), health=50, strength=15)
```

**Add a new item** (in `items.py`):

```python
class Shield(Item):
    """Shield that reduces damage taken"""
    def __init__(self, x: int, y: int):
        super().__init__("Shield", x, y)
        self.char = '['
        self.color = (100, 100, 200)

    def pick_up(self, player):
        player.defense_bonus += 2
        return "Gained Shield! +2 Defense"
```

Then update `dungeon.py` to spawn your new monsters/items in the `generate()` method.

## Installation

1. Clone or download the project
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python roguelike.py
```

## Testing

The project includes comprehensive unit tests using pytest. Run tests with:

```bash
pytest
```

For verbose output with coverage:

```bash
pytest -v --cov=. --cov-report=term-missing
```

Test files are in the `tests/` directory:
- `test_entities.py` - Player and Actor tests
- `test_items.py` - Item pickup and effects
- `test_monsters.py` - Monster initialization and stats
- `test_dungeon.py` - Dungeon generation and layout

## Controls

| Key          | Action                        |
| ------------ | ----------------------------- |
| Arrow Keys   | Move up/down/left/right       |
| `.` (period) | Go down stairs (if available) |
| `ESC`        | Quit game                     |
| `R`          | Restart (when game is over)   |
| `Q`          | Quit (when game is over)      |

## Gameplay

### Combat

Walk into a monster to attack it. Damage is based on your Strength stat plus a random modifier.

### Items

Walk over items to pick them up:

- **Gold ($)**: Currency and score
- **Weapons (/)**: Permanently increase Strength
- **Potions (!)**: Temporarily modify Strength or Health for several turns
- **Amulet of Yendor (\*)**: The goal! Needed to win the game

### Progression

1. Explore each dungeon level
2. Collect items and equipment
3. Defeat monsters
4. Find the stairs (>) and descend to the next level
5. On level 5, find the Amulet of Yendor
6. Return to the stairs and escape to win

### Stats

- **HP**: Your health. If it reaches 0, you die
- **STR**: Your attack power. Increased by weapons, or temporarily by potions
- **Gold**: Collected from the dungeon (used for scoring)

## Game Difficulty

- Enemies have more health and damage on deeper levels
- Stat modifications from potions are temporary (3-8 turns)
- Weapons give permanent bonuses
- Be careful fighting multiple enemies!

## Tips

- Explore thoroughly for items
- Potions can help in tough fights
- Weapons give permanent strength increases
- Track your health and use potions when needed
- The Amulet of Yendor is always on level 5

Enjoy your descent into the dungeon!
