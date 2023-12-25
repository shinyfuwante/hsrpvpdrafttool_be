class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.state = {
                'bans': {1: [], 2: []},
                'picks': {1: [], 2: []},
                'turn_order': [
                    (1, 'ban'), (2, 'ban'),
                    (1, 'pick'), (2, 'pick'), (2, 'pick'), (1, 'pick'),
                    (2, 'ban'), (1, 'ban'),
                    (2, 'pick'), (1, 'pick'), (1, 'pick'), (2, 'pick'),
                    (2, 'pick'), (1, 'pick'), (1, 'pick'), (2, 'pick'),
                    (2, 'pick'), (1, 'pick'), (1, 'pick'), (2, 'pick'),
                    (2, 'pick'),
                ]
            }

    def update_state(self, changes):
        # Update the game state based on the changes
        pass

    def get_state(self):
        # Return the current game state
        return self.state