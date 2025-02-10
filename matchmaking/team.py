from matchmaking import Player
from typing import List

class Team:
    def __init__(self, name: str):
        self.name = name
        self.players: List[Player] = []
        self.faction = "None Selected"


    def add_player(self, player : Player):
        self.players.append(player)

    def average_mmr(self):
        return sum(player.mmr for player in self.players) / len(self.players)

    def total_mmr(self):
        return sum(player.mmr for player in self.players)

    def print(self):
        print(f"{self.name} ({self.faction}):")
        for p in sorted(self.players, key=lambda p: p.mmr, reverse=True):
            print(f" - {p}")
        print(f"Total MMR: {self.total_mmr()}")

    def set_faction(self, faction_name):
        self.faction = faction_name

