from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .internal.game_logic.game_logic import Game
from .internal.enums import MessageType
import json
import random
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)

class GameConsumer(AsyncJsonWebsocketConsumer):
    cache_timeout = 10800 # 3 hours
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
        cache.set(self.game_id, participants, self.cache_timeout)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        # Remove the channel_name from the list of participants in the cache
        participants = cache.get(self.game_id, [])
        participants.remove(self.channel_name)
        cache.set(self.game_id, participants, self.cache_timeout)
        
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
            #coin flip to determine who picks side
            selector = random.choice(participants)
            waiter = participants[0] if participants[1] == selector else participants[1]
            cache.set(f'{self.game_id}_selector', selector, self.cache_timeout)
            cache.set(f'{self.game_id}_waiter', waiter, self.cache_timeout)
            payload = {
                'message_type': MessageType.SIDE_SELECT.value,
                'selector': selector
            }
            message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
            }
            logger.info(f"Sending message to channel {self.channel_name}: {message}")
            await self.channel_layer.group_send(self.group_name, message)
        else:
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message_type': 'error',
                'message': 'error',
            })
    
    async def side_select(self, event):
        print("Received side select message")
        if event['side'] == 0:
            bluePlayer = cache.get(f'{self.game_id}_selector')
            redPlayer = cache.get(f'{self.game_id}_waiter')
        elif event['side'] == 1:
            bluePlayer = cache.get(f'{self.game_id}_waiter')
            redPlayer = cache.get(f'{self.game_id}_selector') 
        else: 
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': 'error',
            })
            return
        game = Game(self.game_id, bluePlayer, redPlayer)
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_START.value,
            'game_state': game.get_state()
        }
        message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
        }
        await self.channel_layer.group_send(self.group_name, message)
        
    
    async def game_state(self, event):
        print('received game_state message')
        await self.send_json(event['message'])
        
    async def draft_ban(self, event):
        print('received ban message')
        game = cache.get(f'{self.game_id}_game')
        res = game.update_state(event['ban'], 'ban')
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'success': res
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.GAME_STATE.value, 'message': payload })
    async def front_end_message(self, event):
        print("received front_end_message")
        await self.send_json(event['message'])
        