from matchmaking import Team

def get_disparity_between_teams(team1: Team, team2: Team):
    return team1.total_mmr() - team2.total_mmr()