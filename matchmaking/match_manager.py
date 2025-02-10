from typing import List, Tuple
import random
import json
import math
from itertools import product
from functools import lru_cache
from matchmaking import Team, Player, Match


# =======================================================
# CACHING FOR BEST CLASS ASSIGNMENT
# =======================================================
def get_players_key(players: List[Player]) -> Tuple:
    """
    Create a hashable key from a list of players.
    Each player's key is a tuple of (player.id, player.mmr, sorted(player.proficiency.items()))
    """
    return tuple((p.id, p.mmr, tuple(sorted(p.proficiency.items()))) for p in players)


@lru_cache(maxsize=None)
def cached_best_class_assignment(players_key: Tuple) -> Tuple[float, Tuple[str, ...]]:
    avg_scores = {"Infantry": 160, "Cavalry": 200, "Archer": 250}
    ideal_counts = {"Cavalry": 1, "Archer": 1, "Infantry": 4}
    penalty_weight = 50  # tuning parameter

    n = len(players_key)
    # Compute an upper bound.
    max_possible = 0
    for entry in players_key:
        # entry = (id, mmr, proficiency_items)
        prof_dict = dict(entry[2])
        max_val = max((prof_dict.get(role, 0) / 10.0) * avg_scores[role]
                      for role in ["Infantry", "Cavalry", "Archer"])
        max_possible += max_val

    best_net_score = -float('inf')
    best_assignment = None
    for assignment in product(["Cavalry", "Infantry", "Archer"], repeat=n):
        if assignment.count("Cavalry") > 2 or assignment.count("Archer") > 2:
            continue
        total_score = 0
        for entry, role in zip(players_key, assignment):
            prof_dict = dict(entry[2])
            total_score += (prof_dict.get(role, 0) / 10.0) * avg_scores[role]
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


def best_class_assignment_cached(players: List[Player]) -> Tuple[float, Tuple[str, ...]]:
    key = get_players_key(players)
    return cached_best_class_assignment(key)


# =======================================================
# TEAM SPLITTING FUNCTIONS
# =======================================================

def compute_objective(team1: Team, team2: Team, gamma: float = 0.1, beta: float = 100, theta: float = 1,
                      HIGH_MMR_THRESHOLD: int = 5000) -> float:
    overall_disparity = abs(team1.total_mmr() - team2.total_mmr())
    sorted_team1 = sorted(team1.players, key=lambda p: p.mmr, reverse=True)
    sorted_team2 = sorted(team2.players, key=lambda p: p.mmr, reverse=True)
    pairwise_disparity = sum(abs(sorted_team1[i].mmr - sorted_team2[i].mmr) for i in range(6))
    high_count_team1 = sum(1 for p in team1.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_count_team2 = sum(1 for p in team2.players if p.mmr >= HIGH_MMR_THRESHOLD)
    high_player_penalty = abs(high_count_team1 - high_count_team2)
    pred_score_team1, _ = best_class_assignment_cached(team1.players)
    pred_score_team2, _ = best_class_assignment_cached(team2.players)
    class_diff = abs(pred_score_team1 - pred_score_team2)
    return overall_disparity + gamma * pairwise_disparity + beta * high_player_penalty + theta * class_diff


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


def improved_team_split(match_players: List, iterations: int) -> Tuple[Team, Team, float]:
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


def find_best_team_split(match_players: List, iterations: int) -> Tuple[Team, Team, float]:
    return improved_team_split(match_players, iterations)


def calculate_total_cost(partition: List[List], iterations: int) -> Tuple[float, List[Tuple[Team, Team]]]:
    total_cost = 0.0
    splits = []
    for group in partition:
        team1, team2, cost = find_best_team_split(group, iterations)
        total_cost += cost
        splits.append((team1, team2))
    return total_cost, splits


# =======================================================
# FACTION MATCHUP HELPERS
# =======================================================

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


# =======================================================
# MATCH OUTCOME PREDICTION
# =======================================================

def determine_match_outcome_probability(team1: Team, team2: Team, faction_win_diff: float,
                                        k1: float = 1.0, k2: float = 1.0, k3: float = 0.1) -> float:
    mmr_diff = (team1.total_mmr() - team2.total_mmr()) / 1000.0
    pred_score_team1, _ = best_class_assignment_cached(team1.players)
    pred_score_team2, _ = best_class_assignment_cached(team2.players)
    pred_margin = (pred_score_team1 - pred_score_team2) / 1000.0
    faction_effect = faction_win_diff / 10.0
    X = k1 * mmr_diff + k2 * pred_margin + k3 * faction_effect
    probability = 1.0 / (1.0 + math.exp(-X))
    return probability


# =======================================================
# OUTER IMPROVEMENT OF PARTITION (Randomized Swaps)
# =======================================================
def improve_partition(partition: List[List], iterations: int = 100, team_split_iterations: int = 20) -> Tuple[
    float, List[List[Player]]]:
    best_cost, best_splits = calculate_total_cost(partition, team_split_iterations)
    best_partition = partition
    for _ in range(iterations):
        i = random.randrange(len(partition))
        j = random.randrange(len(partition))
        if i == j:
            continue
        p = random.randrange(len(partition[i]))
        q = random.randrange(len(partition[j]))
        new_partition = [group[:] for group in partition]
        new_partition[i][p], new_partition[j][q] = new_partition[j][q], new_partition[i][p]
        new_cost, new_splits = calculate_total_cost(new_partition, team_split_iterations)
        if new_cost < best_cost:
            best_cost = new_cost
            best_partition = new_partition
    return best_cost, best_partition


# =======================================================
# GLOBAL MATCHMAKING
# =======================================================

def find_best_global_matches(players: List) -> List[Match]:
    n = len(players)
    if n not in {12, 24, 36, 48}:
        raise ValueError("Invalid number of players. Must be 12, 24, 36, or 48 players.")
    num_matches = n // 12
    partition = [players[i * 12:(i + 1) * 12] for i in range(num_matches)]

    # Determine team split iterations based on player count. Max is 924, 1848, 2772, 3696
    if n == 12:
        team_split_iterations = 924   # Runtime: <1  seconds
    elif n == 24:
        team_split_iterations = 1848  # Runtime: <20 seconds
    elif n == 36:
        team_split_iterations = 2772  # Runtime: <40 seconds
    elif n == 48:
        team_split_iterations = 3696  # Runtime: <60 seconds
    else:
        team_split_iterations = 20  # fallback

    # Improve the partition using randomized swaps.
    best_cost, best_partition = improve_partition(partition, iterations=100,
                                                  team_split_iterations=team_split_iterations)

    # Recalculate best splits from the final partition.
    _, best_splits = calculate_total_cost(best_partition, team_split_iterations)

    matches = []
    map_names = [
        "Xauna", "Echerion", "Trading post", "Town outskirts",
        "Sharis", "Urikskalaar", "Zendyar", "Port Omor"
    ]
    # Set each player's class based on best assignment.
    for team_pair in best_splits:
        for team in team_pair:
            _, assignment = best_class_assignment_cached(team.players)
            for player, role in zip(team.players, assignment):
                player.set_class(role)
    # Load faction matchup data once.
    faction_matchups = load_faction_matchups()

    # For each team pair, compute outcome probability and create the match.
    for i, (team1, team2) in enumerate(best_splits):
        pred_score_team1, _ = best_class_assignment_cached(team1.players)
        pred_score_team2, _ = best_class_assignment_cached(team2.players)
        predicted_margin = pred_score_team1 - pred_score_team2  # Positive means team1 favored by troops.
        faction1, faction2, faction_win_diff = choose_faction_pair_for_margin(faction_matchups, predicted_margin)
        team1.set_faction(faction1)
        team2.set_faction(faction2)
        outcome_prob = determine_match_outcome_probability(team1, team2, faction_win_diff)
        selected_map = random.choice(map_names)
        match = Match(i + 1, team1, team2, selected_map)
        match.set_outcome(outcome_prob)
        matches.append(match)

    return matches
