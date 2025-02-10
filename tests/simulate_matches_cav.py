import json
import random
import statistics
import time
from matchmaking import Player, Team, find_best_global_matches

def load_config():
    config_path = "../config/config-matchmaking.json"
    with open(config_path, "r") as config_file:
        return json.load(config_file)

def generate_cavalry_players(num_players: int):
    """
    Generates a list of players where each player has 10 in Cavalry,
    and low random values (0.0–5.0) in Infantry and Archer.
    MMR is randomized between 2000 and 8000.
    """
    players = []
    classes = ["Cavalry", "Infantry", "Archer"]
    for i in range(num_players):
        proficiency = {cls: 0.0 for cls in classes}
        # Force Cavalry to be 10.
        proficiency["Cavalry"] = 10.0
        # For Infantry and Archer, assign low random values.
        proficiency["Infantry"] = round(random.uniform(0.0, 5.0), 1)
        proficiency["Archer"] = round(random.uniform(0.0, 5.0), 1)
        mmr = random.randint(2000, 8000)
        player_id = f"Player_{i+1}"
        igl = False
        player = Player(proficiency=proficiency, mmr=mmr, player_id=player_id, igl=igl)
        players.append(player)
    players.sort(key=lambda p: p.mmr, reverse=True)
    # Set the top 8 players as in-game leaders.
    for player in players[:8]:
        player.igl = True
    return players

def simulate_match_outcome(matches):
    """
    Simulates outcomes for each match, updating player MMR.
    (This function is from your original test code.)
    """
    disparities = []
    for match in matches:
        t1 = match.team1
        t2 = match.team2
        disparity = abs(t1.total_mmr() - t2.total_mmr())
        disparities.append(disparity)
        match.print()
        if random.random() < 0.5:
            winning_team = t1
            losing_team = t2
        else:
            winning_team = t2
            losing_team = t1
        for player in winning_team.players:
            player.mmr += 25
        for player in losing_team.players:
            player.mmr -= 25
    return disparities

def main():
    NUM_SIMULATIONS = 100
    NUM_PLAYERS = 12  # Must be 12, 24, 36, or 48
    maps_config = load_config()
    players = generate_cavalry_players(NUM_PLAYERS)
    all_disparities = []
    all_outcomes = []
    for sim in range(1, NUM_SIMULATIONS + 1):
        print(f"\n{'=' * 10} Simulation {sim} {'=' * 10}\n")
        start_time = time.perf_counter()
        matches = find_best_global_matches(players)
        sim_disparities = simulate_match_outcome(matches)
        all_disparities.extend(sim_disparities)
        for m in matches:
            all_outcomes.append(m.outcome_probability)
        end_time = time.perf_counter()
        runtime = end_time - start_time
        mean_disp = statistics.mean(sim_disparities)
        median_disp = statistics.median(sim_disparities)
        modes = statistics.multimode(sim_disparities)
        mode_disp = modes[0] if modes else None
        print(f"Simulation {sim} Disparity Statistics: Mean: {mean_disp:.2f}, Median: {median_disp}, Mode: {mode_disp}")
        print(f"Simulation {sim} Runtime: {runtime:.4f} seconds")
        print("=" * 40)
    overall_avg = sum(all_disparities) / len(all_disparities) if all_disparities else 0
    avg_outcome = sum(all_outcomes) / (NUM_SIMULATIONS * (NUM_PLAYERS / 12))
    print(f"\nTotal average disparity: {overall_avg}")
    print(f"Avg Outcome: {avg_outcome * 100:.2f}%")

if __name__ == '__main__':
    main()
