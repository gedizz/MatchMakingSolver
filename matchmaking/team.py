from matchmaking.player import Player
from typing import List

class Team:
    def __init__(self, name: str):
        self.name = name
        self.players: List[Player] = []


    def add_player(self, player : Player):
        self.players.append(player)

    def average_mmr(self):
        return sum(player.mmr for player in self.players) / len(self.players)

    def total_mmr(self):
        return sum(player.mmr for player in self.players)

    def print(self):
        print(f"{self.name}:")
        for p in self.players:
            print(f" - {p}")

