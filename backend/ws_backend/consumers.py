from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .core.game_logic import Game
import json

class GameConsumer(AsyncJsonWebsocketConsumer):
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
    
    async def receive(self, text_data):
        try:
            content = json.loads(text_data)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {text_data}")
            return

        await self.receive_json(content)
        
    async def receive_json(self, content):
        print('received_json')
        game_state = await self.game_state(content)
        # publishes to Redis channel
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'game_state', # determines what method to call.. 
                'game_state': 'test',
                'sender_channel_name': self.channel_name
            }
        )
        pass
    
    async def game_state(self, event):
        print('received game_state message')
        print(event)
        await self.send_json(event['game_state'])

    # Implement methods to handle incoming WebSocket messages and manage game sessions