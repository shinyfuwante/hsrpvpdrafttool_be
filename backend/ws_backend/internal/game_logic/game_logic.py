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
            self.state['bans'][self.state['turn_order'][self.turn_index][0]].append(pick['character'])
            self.turn_index += 1
        else:
            if self.state['turn_order'][self.turn_index][1] != 'pick':
                print("Error: not pick phase")
                return False
            self.state['picks'][self.state['turn_order'][self.turn_index][0]].append(pick['character'])
            self.turn_index += 1
        return True
    
    def sig_eid_change(self, character):
        print(character)
        new_char = character['character']
        team = character['team']
        for team in self.state['picks']:
            for i, char in enumerate(self.state['picks'][team]):
                if char['name'] == new_char['name']:
                    print("found match")
                    self.state['picks'][team][i] = new_char
                    return 
        return
    
    def get_state(self):
        return self.state
    
    def get_turn_player(self):
        return self.state['turn_order'][self.turn_index][0]
    
    def reset_game(self):
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
        self.turn_index = 0
        
    def undo_turn(self):
        if self.turn_index == 0:
            return False
        self.turn_index -= 1
        if self.state['turn_order'][self.turn_index][1] == 'ban':
            self.state['bans'][self.state['turn_order'][self.turn_index][0]].pop()
        else:
            self.state['picks'][self.state['turn_order'][self.turn_index][0]].pop()
        return True
    
    def get_blue(self):
        return self.blue_team
    
    def get_red(self):
        return self.red_team