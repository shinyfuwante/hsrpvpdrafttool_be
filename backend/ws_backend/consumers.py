from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .internal.game_logic.game_logic import Game
from .internal.enums import MessageType
import json
import random
from django.core.cache import cache

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Called when the WebSocket is handshaking
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f'game_{self.game_id}'
            
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Add the channel_name to the list of participants in the cache
        participants = cache.get(self.game_id, [])
        participants.append(self.channel_name)
        cache.set(self.game_id, participants)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        # Remove the channel_name from the list of participants in the cache
        participants = cache.get(self.game_id, [])
        participants.remove(self.channel_name)
        cache.set(self.game_id, participants)
    
    async def receive(self, text_data):
        try:
            content = json.loads(text_data)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {text_data}")
            return

        await self.receive_json(content)
        
    async def receive_json(self, content):
        message_type = content.get('type')

        if message_type is None or not hasattr(self, message_type):
            print(f"Received message with invalid type: {message_type}")
            return

        handler = getattr(self, message_type)
        await handler(content)
        
        
    async def init_game(self, event):
        print("Received init game message")
        participants = cache.get(self.game_id)
        print("participants: " + str(participants))
        if participants and len(participants) == 2:
            print("Assigning sides")
            selector = random.choice(participants)
            print("selected selector: " + selector)
            waiter = participants[0] if participants[1] == selector else participants[1]
            cache.set(f'{self.game_id}_selector', selector)
            print("set selector in cache")
            cache.set(f'{self.game_id}_waiter', waiter)
            print("set waiter in cache")
            await self.channel_layer.group_send(self.group_name, {
                'type': 'front_end_message',
                'message_type': MessageType.SIDE_SELECT.value,
                'selector': selector
            })
            print("sent side select message to group")
        else:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'front_end_message',
                'message_type': 'error',
            })
    
    async def game_state(self, event):
        print('received game_state message')
        print(event)
        await self.send_json(event['game_state'])
        
    async def front_end_message(self, event):
        pass