#!/usr/bin/env python3
"""
Roguelike Game using libtcod
A simple dungeon crawler with monsters, items, and stats.
"""

from game import Game


def main():
    """Entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
