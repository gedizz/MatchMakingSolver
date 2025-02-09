from matchmaking import Player

def print_formatted_player(player: Player):
    print(f"Player {player.id}:")
    print(f"-- MMR: {player.mmr}")
    print(f"-- IGL: {player.igl}")
    print(f"-- Profiencies: Cav({player.proficiency['Cavalry']}) - Inf({player.proficiency['Infantry']}) - Arc({player.proficiency['Archer']})\n")