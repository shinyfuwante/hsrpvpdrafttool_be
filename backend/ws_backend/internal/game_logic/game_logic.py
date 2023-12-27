class Game:
    def __init__(self, game_id, player1, player2):
        self.game_id = game_id
        self.player1 = player1
        self.player2 = player2
        self.state = {
            'bans': {self.player1: [], self.player2: []},
            'picks': {self. player1: [], self.player2: []},
            'turn_order': [
                (self.player1, 'ban'), (self.player2, 'ban'),
                (self.player1, 'pick'), (self.player2, 'pick'), (self.player2, 'pick'), (self.player1, 'pick'),
                (self.player2, 'ban'), (self.player1, 'ban'),
                (self.player2, 'pick'), (self.player1, 'pick'), (self.player1, 'pick'), (self.player2, 'pick'),
                (self.player2, 'pick'), (self.player1, 'pick'), (self.player1, 'pick'), (self.player2, 'pick'),
                (self.player2, 'pick'), (self.player1, 'pick'), (self.player1, 'pick'), (self.player2, 'pick'),
                (self.player2, 'pick'),
            ]
        }

    def update_state(self, changes):
        # Update the game state based on the changes
        pass

    def get_state(self):
        return self.state