from typing import List, Tuple
import random
import json
import math
from itertools import product
from matchmaking import Team, Player, Match


# -------------------------------------------------------
# Helper: Given 6 players, find the best valid class assignment.
#
# Hard limits: ≤2 Cavalry, ≤2 Archer (Infantry is unlimited).
# Predicted score for a player in a role = (proficiency/10) * avg_score,
# where avg_scores are:
#   Infantry: 160, Cavalry: 200, Archer: 250.
#
# The IDEAL assignment is: 1 Cavalry, 1 Archer, 4 Infantry.
#
# To encourage this composition, we subtract a penalty from the total
# predicted score for each unit of deviation from the ideal counts.
#
# We also compute an upper bound (the maximum possible predicted score
# per player, ignoring hard limits) and exit early if that bound is reached.
# -------------------------------------------------------
def best_class_assignment(players: List[Player]) -> Tuple[float, Tuple[str, ...]]:
    avg_scores = {"Infantry": 160, "Cavalry": 200, "Archer": 250}
    ideal_counts = {"Cavalry": 1, "Archer": 1, "Infantry": 4}
    penalty_weight = 50  # tuning parameter

    # Compute an upper bound.
    max_possible = 0
    for player in players:
        max_val = max((player.proficiency.get(role, 0) / 10.0) * avg_scores[role]
                      for role in ["Infantry", "Cavalry", "Archer"])
        max_possible += max_val

    best_net_score = -float('inf')
    best_assignment = None
    for assignment in product(["Cavalry", "Infantry", "Archer"], repeat=len(players)):
        if assignment.count("Cavalry") > 2 or assignment.count("Archer") > 2:
            continue
        total_score = 0
        for player, role in zip(players, assignment):
            prof = player.proficiency.get(role, 0)
            total_score += (prof / 10.0) * avg_scores[role]
        penalty = penalty_weight * (
                abs(assignment.count("Cavalry") - ideal_counts["Cavalry"]) +
                abs(assignment.count("Archer") - ideal_counts["Archer"]) +
                abs(assignment.count("Infantry") - ideal_counts["Infantry"])
        )
        net_score = total_score - penalty
        if net_score > best_net_score:
            best_net_score = net_score
            best_assignment = assignment
            if abs(net_score - max_possible) < 1e-6:
                break
    return best_net_score, best_assignment


# -------------------------------------------------------
# Compute an objective for a candidate split of two teams.
#
# Combines overall MMR disparity, pairwise slot differences, imbalance in high-MMR counts,
# and differences in predicted team scores.
# -------------------------------------------------------
def compute_objective(team1: Team, team2: Team, gamma: float = 0.1, beta: float = 100, theta: float = 1,
                      HIGH_MMR_THRESHOLD: int = 7000) -> float:
    overall_disparity = abs(team1.total_mmr() - team2.total_mmr())
    sorted_team1 = sorted(team1.players, key=lambda p: p.mmr, reverse=True)
    sorted_team2 = sorted(team2.players, key=lambda p: p.mmr, reverse=True)
    pairwise_disparity = sum(abs(sorted_team1[i].mmr - sorted_team2[i].mmr) for i in range(6))
    high_count_team1 = sum(1 for p in team1.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_count_team2 = sum(1 for p in team2.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_player_penalty = abs(high_count_team1 - high_count_team2)
    pred_score_team1, _ = best_class_assignment(team1.players)
    pred_score_team2, _ = best_class_assignment(team2.players)
    class_diff = abs(pred_score_team1 - pred_score_team2)
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
# Limited local search: start with a heuristic split and try random swaps.
# -------------------------------------------------------
def improved_team_split(match_players: List, iterations: int = 50) -> Tuple[Team, Team, float]:
    best_team1, best_team2, best_score = heuristic_team_split(match_players)
    best_team1_players = best_team1.players[:]
    best_team2_players = best_team2.players[:]
    for _ in range(iterations):
        i = random.randrange(6)
        j = random.randrange(6)
        new_team1_players = best_team1_players[:]
        new_team2_players = best_team2_players[:]
        new_team1_players[i], new_team2_players[j] = new_team2_players[j], new_team1_players[i]
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
# Given a partition (list of groups, each of 12 players), compute total cost and splits.
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
# Faction matchup helpers.
# -------------------------------------------------------
def load_faction_matchups(filepath: str = "../config/faction_matchups.json") -> List[dict]:
    with open(filepath, "r") as f:
        return json.load(f)


def choose_faction_pair_for_margin(matchups: List[dict], predicted_margin: float) -> Tuple[str, str, float]:
    best_pair = None
    best_win_diff = None
    min_diff = float('inf')
    for entry in matchups:
        f1 = entry["Faction1"]
        f2 = entry["Faction2"]
        win_diff = entry["WinDifference"]
        diff = abs(predicted_margin + win_diff)
        if diff < min_diff:
            min_diff = diff
            best_pair = (f1, f2)
            best_win_diff = win_diff
    return best_pair[0], best_pair[1], best_win_diff


# -------------------------------------------------------
# Determine the overall match outcome probability.
#
# We combine three factors:
#   - The normalized difference in team MMR.
#   - The normalized difference in predicted troop (class) scores.
#   - The normalized faction matchup win difference.
#
# The overall score is passed through a logistic function to produce a probability.
#
# NOTE: k3 has been reduced to 0.1 so that the faction effect does not overwhelm the other factors.
# -------------------------------------------------------
def determine_match_outcome_probability(team1: Team, team2: Team, faction_win_diff: float,
                                        k1: float = 1.0, k2: float = 1.0, k3: float = 0.1) -> float:
    mmr_diff = (team1.total_mmr() - team2.total_mmr()) / 1000.0
    pred_score_team1, _ = best_class_assignment(team1.players)
    pred_score_team2, _ = best_class_assignment(team2.players)
    pred_margin = (pred_score_team1 - pred_score_team2) / 1000.0
    faction_effect = faction_win_diff / 10.0
    X = k1 * mmr_diff + k2 * pred_margin + k3 * faction_effect
    probability = 1.0 / (1.0 + math.exp(-X))
    return probability


# -------------------------------------------------------
# Given a list of players, partition them into matches (each with 12 players)
# and assign two teams per match such that overall imbalance is minimized.
#
# After teams are balanced (MMR, class assignments), we:
#   - Set each player's class using best_class_assignment.
#   - Load faction matchup data.
#   - For each team pair, compute the predicted troop margin, choose the faction pair
#     that best compensates for the troop margin, and set the teams’ factions.
#   - Compute the overall match outcome probability using the chosen faction matchup's win difference.
#   - Create a Match object and call its set_outcome method so that the outcome is stored.
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
        "Xauna", "Echerion", "Trading post", "Town outskirts",
        "Sharis", "Urikskalaar", "Zendyar", "Port Omor"
    ]
    # Set each player's class based on best assignment.
    for team_pair in best_splits:
        for team in team_pair:
            _, assignment = best_class_assignment(team.players)
            for player, role in zip(team.players, assignment):
                player.set_class(role)
    # Load faction matchup data once.
    faction_matchups = load_faction_matchups()

    # For each team pair, compute outcome probability and create the match.
    for i, (team1, team2) in enumerate(best_splits):
        # Compute predicted troop scores and margin.
        pred_score_team1, _ = best_class_assignment(team1.players)
        pred_score_team2, _ = best_class_assignment(team2.players)
        predicted_margin = pred_score_team1 - pred_score_team2  # Positive means team1 favored by troops.

        # Choose faction pair based on predicted margin.
        faction1, faction2, faction_win_diff = choose_faction_pair_for_margin(faction_matchups, predicted_margin)
        team1.set_faction(faction1)
        team2.set_faction(faction2)

        # Determine the overall match outcome probability.
        outcome_prob = determine_match_outcome_probability(team1, team2, faction_win_diff)

        # Create the Match object.
        selected_map = random.choice(map_names)
        match = Match(i + 1, team1, team2, selected_map)

        # Set the outcome on the match.
        match.set_outcome(outcome_prob)
        matches.append(match)

    return matches
