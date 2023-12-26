from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .internal.game_logic.game_logic import Game
from .internal.enums import MessageType
import json
import random
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)

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
    
    # async def receive(self, text_data):
    #     try:
    #         content = json.loads(text_data)
    #     except json.JSONDecodeError:
    #         print(f"Invalid JSON: {text_data}")
    #         return

    #     await self.receive_json(content)
        
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
        if participants and len(participants) == 2:
            selector = random.choice(participants)
            waiter = participants[0] if participants[1] == selector else participants[1]
            cache.set(f'{self.game_id}_selector', selector)
            cache.set(f'{self.game_id}_waiter', waiter)
            message = {
                'message_type': MessageType.SIDE_SELECT.value,
                'selector': selector
            }
            logger.info(f"Sending message to channel {self.channel_name}: {message}")
            await self.channel_layer.group_send(self.group_name, {'type': "front_end_message", 'message': message})
        else:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'front_end_message',
                'message': 'error',
            })
    
    async def game_state(self, event):
        print('received game_state message')
        print(event)
        await self.channel_layer.group_send(self.group_name, { 'type': 'front_end_message', 'message' : 'world' })
        
    async def front_end_message(self, event):
        print("received front_end_message")
        await self.send_json(event['message'])
        