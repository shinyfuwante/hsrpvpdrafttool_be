from channels.generic.websocket import AsyncWebsocketConsumer
from .core.game_logic import Game

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Called when the WebSocket is handshaking
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f'game_{self.game_id}'
        self.game = Game(self.game_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Implement session handling or game setup logic here

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        pass

    async def receive_json(self, content):
        game_state = await self.update_game_state(content)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'game_state',
                'game_state': game_state
            }
        )
    
    async def game_state(self, event):
        await self.send_json(event['game_state'])

    # Implement methods to handle incoming WebSocket messages and manage game sessions