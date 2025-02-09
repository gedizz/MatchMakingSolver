import json
from matchmaking import Player, Team, find_best_global_matches

test_data_path = "tests/48_player_list.json"

with open(test_data_path, "r") as file:
    players_data = json.load(file)

players = Player.from_json(players_data)


#for player in players:
#    util.print_formatted_player(player)

team_1 = Team("Team 1")
team_2 = Team("Team 2")

for i in range(len(players)):
    if i % 2 == 0:
        team_1.add_player(players[i])
    else:
        team_2.add_player(players[i])


matches = find_best_global_matches(players)

for m in matches:
    m.print()

#team_1.print()
#team_2.print()

#print(f"Team 1 MMR: {team_1.total_mmr()}")
#print(f"Team 2 MMR: {team_2.total_mmr()}")
#print(f"Disparity = {get_disparity_between_teams(team_1, team_2)}")

