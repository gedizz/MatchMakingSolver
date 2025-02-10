import json
import random
import statistics
import time  # Added to measure runtime stats
from matchmaking import Player, Team, find_best_global_matches

def load_config():
    """
    Loads the maps configuration from the ./config folder.
    Adjust the filename if necessary.
    """
    config_path = "../config/config-matchmaking.json"  # Update if your config file has a different name.
    with open(config_path, "r") as config_file:
        return json.load(config_file)

def generate_random_players(num_players: int):
    """
    Generates a list of players with fixed proficiency values:
      - Each player gets a proficiency permutation: one class at 10, one at 5, and one at 0.
      - mmr: a random integer between 2000 and 6000.
      - player_id: a unique identifier string (e.g., "Player_1").
      - igl: a boolean (initially set to False, then the top 8 players by MMR are set to True).
    """
    players = []
    for i in range(num_players):
        # Create a random permutation of the proficiency values [10, 5, 0]
        levels = [10, 5, 0]
        random.shuffle(levels)

        # Assign the values to the classes in a fixed order.
        proficiency = {
            "Cavalry": levels[0],
            "Infantry": levels[1],
            "Archer": levels[2]
        }
        mmr = random.randint(2000, 8000)
        player_id = f"Player_{i + 1}"
        igl = False

        # Create a Player (assumes your Player class accepts these parameters)
        player = Player(proficiency=proficiency, mmr=mmr, player_id=player_id, igl=igl)
        players.append(player)

    # Sort the players in descending order based on their MMR.
    players.sort(key=lambda p: p.mmr, reverse=True)

    # Set the top 8 players' igl attribute to True.
    for player in players[:8]:
        player.igl = True

    return players

def simulate_match_outcome(matches):
    """
    For each match:
      1. Calculate the match disparity (the absolute difference between the total MMRs of the two teams)
      2. Print out the match details (including the selected map, using each team's print method,
         and showing the total MMRs)
      3. Then, randomly choose a winner (team1 or team2) and update players' MMR accordingly:
           - +25 MMR for each player on the winning team
           - -25 MMR for each player on the losing team

    Returns:
        A list of disparity values for the matches.
    """
    disparities = []
    for match in matches:
        t1 = match.team1
        t2 = match.team2

        # Compute disparity based on current MMR totals.
        disparity = abs(t1.total_mmr() - t2.total_mmr())
        disparities.append(disparity)

        # Print match details BEFORE updating any MMR.
        match.print()

        # Now simulate outcome: randomly choose a winner.
        if random.random() < 0.5:
            winning_team = t1
            losing_team = t2
            winning_team_name = "Team 1"
        else:
            winning_team = t2
            losing_team = t1
            winning_team_name = "Team 2"

        print(f"\n{winning_team_name} wins!")
        print("-" * 40)

        # Update MMR values after match outcome.
        for player in winning_team.players:
            player.mmr += 25
        for player in losing_team.players:
            player.mmr -= 25

    return disparities

def main():
    NUM_SIMULATIONS = 10
    NUM_PLAYERS = 48  # Must be 12, 24, 36, or 48 for the matchmaking logic.

    # Load the maps configuration.
    maps_config = load_config()

    # Generate the initial pool of players.
    players = generate_random_players(NUM_PLAYERS)

    # To collect disparity data over all simulation rounds.
    all_disparities = []
    all_outcomes = []

    for sim in range(1, NUM_SIMULATIONS + 1):
        print(f"\n{'=' * 10} Simulation {sim} {'=' * 10}\n")
        # Start timing this simulation.
        start_time = time.perf_counter()

        # Form matches using the current players (with their updated MMRs) and the maps configuration.
        matches = find_best_global_matches(players)

        # Simulate match outcomes and print details.
        sim_disparities = simulate_match_outcome(matches)
        all_disparities.extend(sim_disparities)
        for m in matches:
            all_outcomes.append(m.outcome_probability)

        # Calculate and print simulation statistics: mean, median, and mode.
        mean_disp = statistics.mean(sim_disparities)
        median_disp = statistics.median(sim_disparities)
        modes = statistics.multimode(sim_disparities)
        mode_disp = modes[0] if modes else None


        print(f"\nSimulation {sim} Disparity Statistics:")
        print(f"Mean: {mean_disp:.2f}")
        print(f"Median: {median_disp}")
        print(f"Mode: {mode_disp}")


        # End timing this simulation and print runtime.
        end_time = time.perf_counter()
        runtime = end_time - start_time
        print(f"Simulation {sim} Runtime: {runtime:.4f} seconds")
        print("=" * 40)

    # Compute and print the overall statistics across all simulations.
    if all_disparities:
        overall_avg = sum(all_disparities) / len(all_disparities)
        overall_min = min(all_disparities)
        overall_max = max(all_disparities)
    else:
        overall_avg = overall_min = overall_max = 0

    avg_outcome = sum(all_outcomes) / (NUM_SIMULATIONS * (NUM_PLAYERS / 12))

    print(f"\nTotal average disparity over {NUM_SIMULATIONS} simulations: {overall_avg}")
    print(f"Overall minimum disparity: {overall_min}")
    print(f"Overall maximum disparity: {overall_max}")
    print(f"Avg Outcome: {avg_outcome*100:.2f}%")

if __name__ == '__main__':
    main()
