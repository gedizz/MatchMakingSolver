import random
import statistics
from matchmaking import Player, Team, find_best_global_matches


def generate_random_players(num_players: int):
    """
    Generates a list of players with random attributes.
    Each player has:
      - proficiency: a dict with keys "Cavalry", "Infantry", and "Archer"
      - mmr: an integer between 2000 and 6000
      - player_id: a unique identifier string (e.g., "Player_1")
      - igl: a boolean (initially set to False, then the top 8 players by MMR are set to True)
    """
    players = []
    for i in range(num_players):
        proficiency = {
            "Cavalry": random.choice([0, 5, 10]),
            "Infantry": random.choice([0, 5, 10]),
            "Archer": random.choice([0, 5, 10])
        }
        mmr = random.randint(2000, 6000)
        player_id = f"Player_{i + 1}"
        igl = False
        # Create a player (assumes your Player class accepts these parameters)
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
      2. Print out the match details (using each team's print method and showing the total MMRs)
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
        print(f"\nMatch {match.id} Results:")
        print(f"Disparity: {disparity}")
        print("Team 1:")
        t1.print()
        print(f"Team 1 Total MMR: {t1.total_mmr()}\n")
        print("Team 2:")
        t2.print()
        print(f"Team 2 Total MMR: {t2.total_mmr()}")

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

        # After printing the details, update the MMR values.
        for player in winning_team.players:
            player.mmr += 25
        for player in losing_team.players:
            player.mmr -= 25

    return disparities


def main():
    NUM_SIMULATIONS = 10
    NUM_PLAYERS = 48  # Must be 12, 24, 36, or 48 for the matchmaking logic.

    # Generate the initial pool of players.
    players = generate_random_players(NUM_PLAYERS)

    # To collect disparity data over all simulation rounds.
    all_disparities = []

    for sim in range(1, NUM_SIMULATIONS + 1):
        print(f"\n{'=' * 10} Simulation {sim} {'=' * 10}\n")

        # Form matches using the current players (with their updated MMRs).
        matches = find_best_global_matches(players)

        # Simulate match outcomes and print details.
        sim_disparities = simulate_match_outcome(matches)
        all_disparities.extend(sim_disparities)

        # Calculate and print simulation statistics: mean, median, and mode.
        mean_disp = statistics.mean(sim_disparities)
        median_disp = statistics.median(sim_disparities)
        modes = statistics.multimode(sim_disparities)
        mode_disp = modes[0] if modes else None

        print(f"\nSimulation {sim} Disparity Statistics:")
        print(f"Mean: {mean_disp}")
        print(f"Median: {median_disp}")
        print(f"Mode: {mode_disp}")
        print("=" * 40)

    # Compute and print the overall average disparity across all simulations.
    overall_avg = sum(all_disparities) / len(all_disparities) if all_disparities else 0
    print(f"\nTotal average disparity over {NUM_SIMULATIONS} simulations: {overall_avg}")


if __name__ == '__main__':
    main()
