from itertools import combinations
from matchmaking import Team, Player, Match
from typing import List, Tuple
import random

def find_best_team_split(match_players: List) -> Tuple[Team, Team, float]:
    """
    Given 12 players, exhaustively search for the 6 vs. 6 split that minimizes
    the absolute difference in total MMR between the two teams.

    Returns:
        A tuple (team1, team2, disparity) where disparity is the minimal MMR difference.
    """
    best_split = None
    min_disparity = float('inf')

    # There are 924 possible ways to choose 6 players out of 12.
    for team1_indices in combinations(range(12), 6):
        team1 = Team("Team 1")
        team2 = Team("Team 2")

        for i in range(12):
            if i in team1_indices:
                team1.add_player(match_players[i])
            else:
                team2.add_player(match_players[i])

        disparity = abs(team1.total_mmr() - team2.total_mmr())
        if disparity < min_disparity:
            min_disparity = disparity
            best_split = (team1, team2)

            # Early exit: perfect balance found.
            if min_disparity == 0:
                break
    return best_split[0], best_split[1], min_disparity


def calculate_total_cost(
        partition: List[List]
) -> Tuple[float, List[Tuple[Team, Team]]]:
    """
    Given a partition (list of groups, each of 12 players), compute the cost for each match.
    The cost for a match is defined as the minimal MMR disparity achieved by the optimal
    team split. Returns the sum of disparities (global cost) and the corresponding team splits.
    """
    total_cost = 0.0
    splits = []
    for group in partition:
        team1, team2, cost = find_best_team_split(group)
        total_cost += cost
        splits.append((team1, team2))
    return total_cost, splits


def find_best_global_matches(players: List) -> List[Match]:
    """
    Given a list of players (whose count is 12, 24, 36, or 48), partition them into matches
    (each containing 12 players) and assign two teams per match such that the overall
    MMR imbalance is minimized across all matches.

    This function starts with an initial partition (slicing the players list) and then
    attempts to improve the grouping by swapping players between matches.

    Returns:
        A list of Match objects with balanced team splits.
    """
    n = len(players)
    if n not in {12, 24, 36, 48}:
        raise ValueError("Invalid number of players. Must be 12, 24, 36, or 48 players.")

    num_matches = n // 12
    # Initial partition: simply slice the players list.
    partition = [players[i * 12:(i + 1) * 12] for i in range(num_matches)]
    best_cost, best_splits = calculate_total_cost(partition)

    improved = True
    # Iterative improvement: try swapping players between different groups.
    while improved:
        improved = False
        # Loop over every pair of matches.
        for i in range(num_matches):
            for j in range(i + 1, num_matches):
                # Loop over each player in match i and each player in match j.
                for p in range(12):
                    for q in range(12):
                        # Create a new partition by copying the current partition.
                        new_partition = [group[:] for group in partition]

                        # Swap one player from match i with one from match j.
                        new_partition[i][p], new_partition[j][q] = new_partition[j][q], new_partition[i][p]

                        new_cost, new_splits = calculate_total_cost(new_partition)
                        if new_cost < best_cost:
                            best_cost = new_cost
                            partition = new_partition
                            best_splits = new_splits
                            improved = True
                            # Once a beneficial swap is found, break out to restart scanning.
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    # Finally, create Match objects for each partition using the computed best splits.
    matches = []

    # generate a random map
    map_names = [
        "Xauna",
        "Echerion",
        "Trading post",
        "Town outskirts",
        "Sharis",
        "Urikskalaar",
        "Zendyar",
        "Port Omor"
    ]

    # Pick a random map from the list.
    selected_map = random.choice(map_names)

    for i, (team1, team2) in enumerate(best_splits):
        selected_map = random.choice(map_names)
        matches.append(Match(i + 1, team1, team2, selected_map))
    return matches