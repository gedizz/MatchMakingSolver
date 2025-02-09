from .team import Team
from .round import Round

class Game:
    def __init__(self, game_id: int, teams: list[Team]):
        """
        Initializes a Game object.

        :param game_id: Unique identifier for the game.
        :param teams: List of Team objects participating in the game.
        """
        self.game_id = game_id
        self.teams = teams
        self.rounds = []
        self.winner = None

    def add_round(self, round_obj: Round):
        """
        Adds a round to the game.

        :param round_obj: Round object to be added.
        """
        self.rounds.append(round_obj)

    def decide_winner(self):
        """
        Decides the winner of the game based on round outcomes.
        """
        scores = {team.name: 0 for team in self.teams}

        for round_obj in self.rounds:
            scores[round_obj.winner.name] += 1

        self.winner = max(scores, key=scores.get)

    def __repr__(self):
        return f"Game(game_id={self.game_id}, winner={self.winner}, rounds={len(self.rounds)})"
