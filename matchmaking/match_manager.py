from itertools import combinations
from matchmaking.team import Team
from typing import List, Tuple
from matchmaking.player import Player
from matchmaking.match import Match


def find_best_team_splits(players: List[Player]) -> List[Match]:
    n = len(players)
    # Validate player count: must be exactly 12, 24, 36, or 48.
    if n not in {12, 24, 36, 48}:
        raise ValueError("Invalid number of players. Must be 12, 24, 36, or 48 players.")

    num_matches = n // 12  # Each match consists of 12 players.
    matches: List[Match] = []

    # Process each match's players separately.
    for match_index in range(num_matches):
        # Slice the players list to get the 12 players for this match.
        match_players = players[match_index * 12: (match_index + 1) * 12]

        best_split = None
        min_disparity = float('inf')

        # For each possible combination of 6 players (Team 1) out of 12.
        for team1_indices in combinations(range(12), 6):
            team1 = Team(f"Team 1")
            team2 = Team(f"Team 2")

            # Distribute the 12 players between the two teams.
            for i in range(12):
                if i in team1_indices:
                    team1.add_player(match_players[i])
                else:
                    team2.add_player(match_players[i])

            # Calculate the disparity for this split.
            disparity = abs(team1.total_mmr() - team2.total_mmr())
            if disparity < min_disparity:
                min_disparity = disparity
                best_split = (team1, team2)

        # Once the best split is found for this match, create a Match object.
        matches.append(Match(match_index + 1, best_split[0], best_split[1]))

    return matches