class Game:
    def __init__(self, game_id, player1, player2):
        self.game_id = game_id
        self.blue_team = player1
        self.red_team = player2
        self.turn_index = 0
        self.state = {
            'bans': {"blue_team": [], "red_team": []},
            'picks': {"blue_team": [], "red_team": []},
            'turn_order': [
                ("blue_team", 'ban'), ("red_team", 'ban'),
                ("blue_team", 'pick'), ("red_team", 'pick'), ("red_team", 'pick'), ("blue_team", 'pick'),
                ("red_team", 'ban'), ("blue_team", 'ban'),
                ("red_team", 'pick'), ("blue_team", 'pick'), ("blue_team", 'pick'), ("red_team", 'pick'),
                ("red_team", 'pick'), ("blue_team", 'pick'), ("blue_team", 'pick'), ("red_team", 'pick'),
                ("red_team", 'pick'), ("blue_team", 'pick'), ("blue_team", 'pick'), ("red_team", 'pick'),
                ("red_team", 'pick'),
            ]
        }

    def update_state(self, pick, pick_type):
        if pick['team'] != self.state['turn_order'][self.turn_index][0]:
            print("Error: not this team's turn")
            return False
        if pick_type == 'ban':
            if self.state['turn_order'][self.turn_index][1] != 'ban':
                print("Error: not ban phase")
                return False
            self.state['bans'][self.state['turn_order'][self.turn_index][0]].append(pick)
            self.turn_index += 1
        else:
            if self.state['turn_order'][self.turn_index][1] != 'pick':
                print("Error: not pick phase")
                return False
            self.state['picks'][self.state['turn_order'][self.turn_index][0]].append(pick)
            self.turn_index += 1
        return True

    def get_state(self):
        return self.state
    
    def get_turn_index(self):
        return self.turn_index