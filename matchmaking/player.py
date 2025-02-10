import json
from typing import Dict, List

class Player:
    def __init__(self, player_id: str, proficiency: Dict[str, int], mmr: int, igl: bool):
        self.id = player_id
        self.proficiency = proficiency
        self.mmr = mmr
        self .igl = igl
        self.selected_class = "None"

    def __repr__(self):
        return f"Player(id={self.id}, mmr={self.mmr}, proficiency={self.proficiency}, igl={self.igl} Selected: {self.selected_class}"

    @classmethod
    def from_json(cls, json_data: List[Dict]):
        return [cls(player["id"], player["proficiency"], player["mmr"], player["igl"]) for player in json_data]

    def set_class(self, class_name):
        self.selected_class = class_name