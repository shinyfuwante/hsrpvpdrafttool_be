from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .internal.game_logic.game_logic import Game
from .internal.enums import MessageType, ErrorType
import random
from django.core.cache import cache
import json
import logging
from urllib.parse import parse_qs
import os
logger = logging.getLogger(__name__)

class GameConsumer(AsyncJsonWebsocketConsumer):
    cache_timeout = 10800 # 3 hours
    async def load_json(self, directory, filename):
        with open(os.path.join(directory, filename)) as f:
            return json.load(f)
        
    async def connect(self):
        # Called when the WebSocket is handshaking
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        participants = cache.get(f'{self.game_id}_cids', [])
        self.group_name = f'game_{self.game_id}'
        connections = cache.get(f'{self.game_id}_connections', [])
        query_string = parse_qs(self.scope['query_string'].decode('utf8'))
        print(query_string)
        
        if cache.get(f'{self.game_id}_rule_set'):
            self.rule_set = cache.get(f'{self.game_id}_rule_set')
        else:
            self.rule_set = query_string.get('ruleSet', ['phd_standard'])[0]
            print(self.rule_set)
            cache.set(f'{self.game_id}_rule_set', self.rule_set, self.cache_timeout)
            
        self.cid = query_string.get('cid')[0]
        if self.cid in connections: # they are trying to connect on same connection
            # send message saying they need to invite a friend
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.ERROR.value,
                    'error_type': ErrorType.SAME_CONNECTION.value,
                    'error': 'Cannot connect on same connection. Please invite a friend to join.',
                },
            })
            return
        elif self.cid not in participants and len(participants) == 2: # they are trying to connect to a full game   
            # send message saying game is full
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.ERROR.value,
                    'error_type': ErrorType.FULL_GAME.value,
                    'error': 'Game is full.',
                },
            })
        else: #it's a homie and game has started
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            if self.cid in participants: 
                # return game_state to connecting client
                await self.channel_layer.group_send(self.group_name, {
                    'type': MessageType.RECONNECT.value,
                })
                connections.append(self.cid)
                cache.set(f'{self.game_id}_connections', connections, self.cache_timeout)
                return 
        rule_set_dir = os.path.join('ws_backend', 'internal', 'rule_sets', self.rule_set)
        characters = await self.load_json(rule_set_dir, 'characters.json')
        light_cones = await self.load_json(rule_set_dir, 'light_cones.json')
        cache.set(f'{self.game_id}_characters', characters, self.cache_timeout)
        cache.set(f'{self.game_id}_light_cones', light_cones, self.cache_timeout)
        
        # Add the channel_name to the list of connectinos in the cache
        connections.append(self.cid)
        cache.set(f'{self.game_id}_connections', connections, self.cache_timeout)
        if len(participants) < 2: 
            participants.append(self.cid)
            cache.set(f'{self.game_id}_cids', participants, self.cache_timeout)
        if len(participants) == 2:
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.GAME_READY.value,
            })
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        connections = cache.get(f'{self.game_id}_connections')
        connections.remove(self.cid)
        cache.set(f'{self.game_id}_connections', connections, self.cache_timeout)
        if len(connections) == 0:
            print("Deleting game from cache")
            cache.delete_many([f'{self.game_id}_selector', f'{self.game_id}_waiter', f'{self.game_id}_game', f'{self.game_id}_rule_set', f'{self.game_id}_characters', f'{self.game_id}_light_cones', f'{self.game_id}_connections', f'{self.game_id}_cids'])
        elif len(connections) == 1:
            print("Waiting for reconnection")
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.RECONNECT.value,
                    'message': 'Waiting for opponent to reconnect.',
                },
            })
            
    async def reconnect(self, event):
        print("Received reconnect message")
        game = cache.get(f'{self.game_id}_game')
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index,
            'team': 'blue_team' if game.blue_team == self.cid else 'red_team'
        }
        message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
        }
        await self.send_json(message)
    async def receive_json(self, content):
        message_type = content.get('type')

        if message_type is None or not hasattr(self, message_type):
            print(f"Received message with invalid type: {message_type}")
            return

        handler = getattr(self, message_type)
        await handler(content)
        
    async def game_ready(self, event):
        print("Received game ready message")
        participants = cache.get(f'{self.game_id}_cids')
        if participants and len(participants) == 2:
            if not cache.get(f'{self.game_id}_selector'):
                selector = random.choice(participants)
                waiter = participants[0] if participants[1] == selector else participants[1]
                cache.set(f'{self.game_id}_selector', selector, self.cache_timeout)
                cache.set(f'{self.game_id}_waiter', waiter, self.cache_timeout)
            selector = cache.get(f'{self.game_id}_selector')
            message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.GAME_READY.value,
                    'cid': self.cid,
                    'selector': selector,
                    'rule_set': cache.get(f'{self.game_id}_rule_set'),
                    'characters': cache.get(f'{self.game_id}_characters'),
                    'light_cones': cache.get(f'{self.game_id}_light_cones')
                }
            }
            await self.send_json(message)
    
    async def side_select(self, event):
        print("Received side select message")
        if event['side'] == "blue":
            bluePlayer = cache.get(f'{self.game_id}_selector')
            redPlayer = cache.get(f'{self.game_id}_waiter')
        elif event['side'] == "red":
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
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'blue_team': bluePlayer,
            'red_team': redPlayer
        }
        message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
        }
        await self.channel_layer.group_send(self.group_name, message)
    
    async def reset_game(self, event):
        print("Received reset game message")
        game = cache.get(f'{self.game_id}_game')
        game.reset_game()
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index
        }
        message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
        }
        await self.channel_layer.group_send(self.group_name, message)
    
    async def undo(self, event):
        print("Received undo message")
        game = cache.get(f'{self.game_id}_game')
        game.undo_turn()
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index
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
        res = game.update_state(event, 'ban')
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'success': res,
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.FRONT_END_MESSAGE.value, 'message': payload })
    
    async def draft_pick(self, event):
        print('received pick message')
        game = cache.get(f'{self.game_id}_game')
        res = game.update_state(event, 'pick')
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'success': res,
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.FRONT_END_MESSAGE.value, 'message': payload })
    
    async def sig_eid_change(self, event):
        print('received sig_eid_change message')
        game = cache.get(f'{self.game_id}_game')
        game.sig_eid_change(event)
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.FRONT_END_MESSAGE.value, 'message': payload })
        
    async def front_end_message(self, event):
        print("received front_end_message")
        await self.send_json(event)
        