import json
from matchmaking import Player, Team, find_best_global_matches

# Load the configuration from the ./config folder.
config_path = "./config/config-matchmaking.json"  # Update this if your config file has a different name.
with open(config_path, "r") as config_file:
    maps_config = json.load(config_file)

# Load player data.
test_data_path = "tests/12_all_inf.json"
with open(test_data_path, "r") as file:
    players_data = json.load(file)

# Convert the JSON player data into Player objects.
players = Player.from_json(players_data)

# Find the best global matches using both the players and the maps configuration.
matches = find_best_global_matches(players)

# Print out each match. The Match object now includes a map name.
for m in matches:
    m.print()

# (Optional alternative code that you previously used for testing.)
# team_1 = Team("Team 1")
# team_2 = Team("Team 2")
# for i in range(len(players)):
#     if i % 2 == 0:
#         team_1.add_player(players[i])
#     else:
#         team_2.add_player(players[i])
#
# team_1.print()
# team_2.print()
