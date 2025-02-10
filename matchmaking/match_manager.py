from typing import List, Tuple
import random
from itertools import combinations  # (Retained for other parts if needed)
from matchmaking import Team, Player, Match


# -------------------------------------------------------
# Common objective function for evaluating a team split.
# -------------------------------------------------------
def compute_objective(team1: Team, team2: Team, gamma: float = 0.1, beta: float = 100,
                      HIGH_MMR_THRESHOLD: int = 7000) -> float:
    # Overall MMR disparity.
    overall_disparity = abs(team1.total_mmr() - team2.total_mmr())

    # Pairwise slot differences: sort players by MMR and compare corresponding slots.
    sorted_team1 = sorted(team1.players, key=lambda p: p.mmr, reverse=True)
    sorted_team2 = sorted(team2.players, key=lambda p: p.mmr, reverse=True)
    pairwise_disparity = sum(abs(sorted_team1[i].mmr - sorted_team2[i].mmr) for i in range(6))

    # Count high-MMR players and penalize uneven distributions.
    high_count_team1 = sum(1 for p in team1.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_count_team2 = sum(1 for p in team2.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_player_penalty = abs(high_count_team1 - high_count_team2)

    return overall_disparity + gamma * pairwise_disparity + beta * high_player_penalty


# -------------------------------------------------------
# Heuristic split: sort by MMR and assign players alternately.
# -------------------------------------------------------
def heuristic_team_split(match_players: List) -> Tuple[Team, Team, float]:
    sorted_players = sorted(match_players, key=lambda p: p.mmr, reverse=True)
    team1 = Team("Team 1")
    team2 = Team("Team 2")
    for i, player in enumerate(sorted_players):
        if i % 2 == 0:
            team1.add_player(player)
        else:
            team2.add_player(player)
    objective = compute_objective(team1, team2)
    return team1, team2, objective


# -------------------------------------------------------
# Local search improvement: try a limited number of random swaps.
# -------------------------------------------------------
def improved_team_split(match_players: List, iterations: int = 50) -> Tuple[Team, Team, float]:
    # Start with the heuristic split.
    best_team1, best_team2, best_score = heuristic_team_split(match_players)

    # Extract lists of players for easier swapping.
    best_team1_players = best_team1.players[:]
    best_team2_players = best_team2.players[:]

    for _ in range(iterations):
        # Randomly select one player from each team.
        i = random.randrange(6)
        j = random.randrange(6)

        # Copy the current best lists and swap the selected players.
        new_team1_players = best_team1_players[:]
        new_team2_players = best_team2_players[:]
        new_team1_players[i], new_team2_players[j] = new_team2_players[j], new_team1_players[i]

        # Rebuild new team objects from the swapped lists.
        new_team1 = Team("Team 1")
        new_team2 = Team("Team 2")
        for p in new_team1_players:
            new_team1.add_player(p)
        for p in new_team2_players:
            new_team2.add_player(p)

        # Compute the new objective.
        new_score = compute_objective(new_team1, new_team2)
        if new_score < best_score:
            best_score = new_score
            best_team1_players = new_team1_players
            best_team2_players = new_team2_players

    # Rebuild the final teams from the best player lists.
    final_team1 = Team("Team 1")
    final_team2 = Team("Team 2")
    for p in best_team1_players:
        final_team1.add_player(p)
    for p in best_team2_players:
        final_team2.add_player(p)

    return final_team1, final_team2, best_score


# -------------------------------------------------------
# Use the improved team split in place of the exhaustive search.
# -------------------------------------------------------
def find_best_team_split(match_players: List) -> Tuple[Team, Team, float]:
    return improved_team_split(match_players, iterations=50)


# -------------------------------------------------------
# The remainder of your file remains largely the same.
# -------------------------------------------------------
def calculate_total_cost(partition: List[List]) -> Tuple[float, List[Tuple[Team, Team]]]:
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

    for i, (team1, team2) in enumerate(best_splits):
        selected_map = random.choice(map_names)
        matches.append(Match(i + 1, team1, team2, selected_map))
    return matches
