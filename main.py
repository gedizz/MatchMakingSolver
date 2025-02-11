import json
import sys
from matchmaking import Player, Team, Match, find_best_global_matches

# Load the maps configuration from the ./config folder.
config_path = "./config/config-matchmaking.json"  # Adjust if needed.
with open(config_path, "r") as config_file:
    maps_config = json.load(config_file)

# Load player data.
if len(sys.argv) > 1:
    players_data_path = sys.argv[1]
else:
    players_data_path = "tests/12_all_inf.json"  # Default file.
with open(players_data_path, "r") as file:
    players_data = json.load(file)

# Convert the JSON player data into Player objects.
players = Player.from_json(players_data)

# Find the best global matches.
matches = find_best_global_matches(players)

# Build output JSON for each match.
output_matches = []
for m in matches:
    team1_ids = [p.id for p in m.team1.players]
    team2_ids = [p.id for p in m.team2.players]
    match_obj = {
        "match_id": m.id,
        "map": m.map,
        "team1": {
            "player_ids": team1_ids,
            "faction": m.team1.faction
        },
        "team2": {
            "player_ids": team2_ids,
            "faction": m.team2.faction
        },
        "outcome_probability": m.outcome_probability
    }
    output_matches.append(match_obj)

# Print the JSON result.
print(json.dumps({"matches": output_matches}))
