from .game import Game
from .team import Team
from utility.statistic_helpers import get_disparity_between_teams


class Match:
    def __init__(self, id: int, team1: Team, team2: Team, map: str):
        """
        Initializes a Match object.

        :param match_id: Unique identifier for the match.
        :param games_required_to_win: Number of games needed to win the match.
        """
        self.id = id
        self.games = []
        #self.games_required_to_win = games_required_to_win
        self.winner = None
        self.team1 = team1
        self.team2 = team2
        self.map = map

    def add_game(self, game: Game):
        """
        Adds a game to the match.

        :param game: Game object to be added.
        """
        self.games.append(game)



    #def __repr__(self):
        #return f"Match(match_id={self.match_id}, winner={self.winner}, games={len(self.games)})"

    def print(self):
        print(f"\n########### Match {self.id} ###########\n")
        print(f"Map: {self.map}")
        self.team1.print()
        self.team2.print()
        print(f"MMR Disparity: {get_disparity_between_teams(self.team1, self.team2)}")
        print("-" * 40)

    def change_map(self, new_map):
        self.map = new_map
