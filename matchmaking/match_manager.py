from typing import List, Tuple
import random
from itertools import product
from matchmaking import Team, Player, Match

# -------------------------------------------------------
# Helper: Given 6 players, find the best valid class assignment.
#
# Hard limits: ≤2 Cavalry, ≤2 Archer (Infantry is unlimited).
# Predicted score for a player in a role = (proficiency/10) * avg_score,
# where avg_scores are given by:
#   Infantry: 160, Cavalry: 200, Archer: 250.
#
# The IDEAL assignment is: 1 Cavalry, 1 Archer, 4 Infantry.
#
# To encourage this composition, we subtract a penalty from the total
# predicted score for each unit of deviation from the ideal counts.
#
# We also compute an upper bound (the maximum possible predicted score
# per player, ignoring hard limits) and if we hit that bound we exit early.
# -------------------------------------------------------
def best_class_assignment(players: List[Player]) -> Tuple[float, Tuple[str, ...]]:
    avg_scores = {"Infantry": 160, "Cavalry": 200, "Archer": 250}
    # Ideal counts for a team of 6.
    ideal_counts = {"Cavalry": 1, "Archer": 1, "Infantry": 4}
    penalty_weight = 50  # Tuning parameter: adjust as needed.

    # Compute an upper bound by summing each player's maximum possible predicted score.
    max_possible = 0
    for player in players:
        max_val = max((player.proficiency.get(role, 0) / 10.0) * avg_scores[role]
                      for role in ["Infantry", "Cavalry", "Archer"])
        max_possible += max_val

    best_net_score = -float('inf')
    best_assignment = None
    # Iterate over all possible assignments for the 6 players.
    for assignment in product(["Cavalry", "Infantry", "Archer"], repeat=len(players)):
        # Enforce hard limits.
        if assignment.count("Cavalry") > 2 or assignment.count("Archer") > 2:
            continue

        total_score = 0
        for player, role in zip(players, assignment):
            prof = player.proficiency.get(role, 0)
            total_score += (prof / 10.0) * avg_scores[role]

        # Compute penalty for deviation from the ideal composition.
        penalty = penalty_weight * (
            abs(assignment.count("Cavalry") - ideal_counts["Cavalry"]) +
            abs(assignment.count("Archer") - ideal_counts["Archer"]) +
            abs(assignment.count("Infantry") - ideal_counts["Infantry"])
        )
        net_score = total_score - penalty

        if net_score > best_net_score:
            best_net_score = net_score
            best_assignment = assignment

            # Early exit: if net_score is nearly equal to max_possible, stop searching.
            if abs(net_score - max_possible) < 1e-6:
                break

    return best_net_score, best_assignment


# -------------------------------------------------------
# Compute an objective for a candidate split of two teams.
#
# The objective combines:
#   - Overall MMR disparity,
#   - Pairwise slot differences,
#   - A penalty for imbalance in the number of high-MMR players,
#   - And a penalty for differences in predicted team scores (using best_class_assignment).
#
# gamma, beta, and theta are tuning parameters.
# -------------------------------------------------------
def compute_objective(team1: Team, team2: Team, gamma: float = 0.1, beta: float = 100, theta: float = 1,
                      HIGH_MMR_THRESHOLD: int = 7000) -> float:
    # Overall MMR disparity.
    overall_disparity = abs(team1.total_mmr() - team2.total_mmr())

    # Pairwise slot differences (after sorting players by MMR descending).
    sorted_team1 = sorted(team1.players, key=lambda p: p.mmr, reverse=True)
    sorted_team2 = sorted(team2.players, key=lambda p: p.mmr, reverse=True)
    pairwise_disparity = sum(abs(sorted_team1[i].mmr - sorted_team2[i].mmr) for i in range(6))

    # Penalty for imbalance in number of high-MMR players.
    high_count_team1 = sum(1 for p in team1.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_count_team2 = sum(1 for p in team2.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_player_penalty = abs(high_count_team1 - high_count_team2)

    # Compute best predicted team score (using our best_class_assignment function).
    pred_score_team1, _ = best_class_assignment(team1.players)
    pred_score_team2, _ = best_class_assignment(team2.players)
    class_diff = abs(pred_score_team1 - pred_score_team2)

    # Total objective.
    return overall_disparity + gamma * pairwise_disparity + beta * high_player_penalty + theta * class_diff


# -------------------------------------------------------
# Fast heuristic split: sort by MMR and alternate assignment.
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
    obj = compute_objective(team1, team2)
    return team1, team2, obj


# -------------------------------------------------------
# Limited local search: start with a heuristic split and try random swaps between the two teams.
# -------------------------------------------------------
def improved_team_split(match_players: List, iterations: int = 50) -> Tuple[Team, Team, float]:
    best_team1, best_team2, best_score = heuristic_team_split(match_players)
    best_team1_players = best_team1.players[:]
    best_team2_players = best_team2.players[:]

    for _ in range(iterations):
        # Randomly select one player from each team to swap.
        i = random.randrange(6)
        j = random.randrange(6)
        new_team1_players = best_team1_players[:]
        new_team2_players = best_team2_players[:]
        new_team1_players[i], new_team2_players[j] = new_team2_players[j], new_team1_players[i]

        # Rebuild teams.
        new_team1 = Team("Team 1")
        new_team2 = Team("Team 2")
        for p in new_team1_players:
            new_team1.add_player(p)
        for p in new_team2_players:
            new_team2.add_player(p)

        new_score = compute_objective(new_team1, new_team2)
        if new_score < best_score:
            best_score = new_score
            best_team1_players = new_team1_players
            best_team2_players = new_team2_players

    final_team1 = Team("Team 1")
    final_team2 = Team("Team 2")
    for p in best_team1_players:
        final_team1.add_player(p)
    for p in best_team2_players:
        final_team2.add_player(p)

    return final_team1, final_team2, best_score


# -------------------------------------------------------
# Use the improved team split instead of exhaustive search.
# -------------------------------------------------------
def find_best_team_split(match_players: List) -> Tuple[Team, Team, float]:
    return improved_team_split(match_players, iterations=50)


# -------------------------------------------------------
# Given a partition (list of groups, each of 12 players), compute the total cost
# and the corresponding team splits.
# -------------------------------------------------------
def calculate_total_cost(partition: List[List]) -> Tuple[float, List[Tuple[Team, Team]]]:
    total_cost = 0.0
    splits = []
    for group in partition:
        team1, team2, cost = find_best_team_split(group)
        total_cost += cost
        splits.append((team1, team2))
    return total_cost, splits


# -------------------------------------------------------
# Given a list of players, partition them into matches (each with 12 players)
# and assign two teams per match such that overall imbalance is minimized.
#
# After the teams are balanced in terms of MMR and predicted performance (with class
# assignments considered), we also set each player's class using their best assignment.
# -------------------------------------------------------
def find_best_global_matches(players: List) -> List[Match]:
    n = len(players)
    if n not in {12, 24, 36, 48}:
        raise ValueError("Invalid number of players. Must be 12, 24, 36, or 48 players.")

    num_matches = n // 12
    partition = [players[i * 12:(i + 1) * 12] for i in range(num_matches)]
    best_cost, best_splits = calculate_total_cost(partition)

    improved = True
    while improved:
        improved = False
        for i in range(num_matches):
            for j in range(i + 1, num_matches):
                for p in range(12):
                    for q in range(12):
                        new_partition = [group[:] for group in partition]
                        new_partition[i][p], new_partition[j][q] = new_partition[j][q], new_partition[i][p]
                        new_cost, new_splits = calculate_total_cost(new_partition)
                        if new_cost < best_cost:
                            best_cost = new_cost
                            partition = new_partition
                            best_splits = new_splits
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

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

    # Before creating Match objects, set each player's class based on best assignment.
    for team_pair in best_splits:
        for team in team_pair:
            _, assignment = best_class_assignment(team.players)
            for player, role in zip(team.players, assignment):
                player.set_class(role)

    for i, (team1, team2) in enumerate(best_splits):
        selected_map = random.choice(map_names)
        matches.append(Match(i + 1, team1, team2, selected_map))

    return matches
