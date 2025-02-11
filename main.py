import json
import sys
from matchmaking import Player, Team, find_best_global_matches

# Load the maps configuration (if needed)
config_path = "./config/config-matchmaking.json"  # Ensure this file exists in MatchMakingSolver/config/
with open(config_path, "r") as config_file:
    maps_config = json.load(config_file)

# If a player data file is provided as a command-line argument, use it; otherwise, use a default.
if len(sys.argv) > 1:
    players_data_path = sys.argv[1]
else:
    players_data_path = "tests/24_player_list.json"  # default file path; adjust as needed

with open(players_data_path, "r") as file:
    players_data = json.load(file)

# Convert the JSON player data into Player objects.
players = Player.from_json(players_data)

# Validate the number of players.
n = len(players)
if n not in [12, 24, 36, 48]:
    print(json.dumps({"error": f"Invalid number of players: {n}. Must be 12, 24, 36, or 48."}))
    sys.exit(1)

# Find the best global matches (this should return a list of Match objects).
matches = find_best_global_matches(players)

# Build the output JSON.
result = []
for m in matches:
    team1_ids = [p.id for p in m.team1.players]
    team2_ids = [p.id for p in m.team2.players]
    result.append({"team1": team1_ids, "team2": team2_ids})

# Output the JSON object to stdout.
print(json.dumps({"matches": result}))
