#!/usr/bin/env python3
"""
Roguelike Game using libtcod
A simple dungeon crawler with monsters, items, and stats.
"""

from game import Game
from leaderboard import Leaderboard


def show_menu():
    """Show main menu"""
    print("\n=== ROGUELIKE DUNGEON ===\n")
    print("1. Play Game")
    print("2. View Leaderboard")
    print("3. Exit")
    print("\nChoice: ", end="", flush=True)
    return input().strip()


def main():
    """Entry point"""
    leaderboard = Leaderboard()
    
    while True:
        choice = show_menu()
        
        if choice == "1":
            print("\nStarting game...\n")
            game = Game()
            game.run()
        elif choice == "2":
            print("\n" + leaderboard.get_formatted_leaderboard())
            print()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
