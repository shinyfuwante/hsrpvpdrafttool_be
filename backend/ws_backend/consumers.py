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
        
        if cache.get(f'{self.game_id}_ruleSetSelection'):
            self.rule_set_selection = cache.get(f'{self.game_id}_ruleSetSelection')
        else:
            self.rule_set_selection = query_string.get('ruleSetSelection', ['phd_standard'])[0]
            print(self.rule_set_selection)
            cache.set(f'{self.game_id}_ruleSetSelection', self.rule_set_selection, self.cache_timeout)
            
        self.cid = query_string.get('cid')[0]
        print("cid: ", self.cid)
        if connections and self.cid in connections: # they are trying to connect on same connection
            # send message saying they need to invite a friend
            print('Cannot connect on same connection')
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.ERROR.value,
                    'error_type': ErrorType.SAME_CONNECTION.value,
                    'error': 'Cannot connect on same connection. Please invite a friend to join.',
                },
            })
            self.cid = "error"
            return
        elif self.cid not in connections and len(connections) == 2: # they are trying to connect to a full game   
            # send message saying game is full
            print('Game is full')
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.ERROR.value,
                    'error_type': ErrorType.FULL_GAME.value,
                    'error': 'Game is full.',
                },
            })
            return
        else: #it's a homie and game has started
            print('Adding to group')
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            if self.cid in participants: 
                print("reconnected")
                # return game_state to connecting client
                connections.append(self.cid)
                cache.set(f'{self.game_id}_connections', connections, self.cache_timeout)
                await self.channel_layer.group_send(self.group_name, {
                    'type': MessageType.RECONNECT.value,
                })
                return 
        
        # Add the channel_name to the list of connectinos in the cache
        connections.append(self.cid)
        cache.set(f'{self.game_id}_connections', connections, self.cache_timeout)
        if len(participants) < 2: 
            print("adding participant, now there are", len(participants) + 1, "participants")
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
        if self.cid in connections:
            connections.remove(self.cid)
            cache.set(f'{self.game_id}_connections', connections, self.cache_timeout)
        participants = cache.get(f'{self.game_id}_cids')
        if len(connections) == 0:
            print("Deleting game from cache")
            cache.delete_many([f'{self.game_id}_selector', f'{self.game_id}_waiter', f'{self.game_id}_game', f'{self.game_id}_rule_set', f'{self.game_id}_characters', f'{self.game_id}_light_cones', f'{self.game_id}_connections', f'{self.game_id}_cids'])
        elif len(connections) == 1 and len(participants) == 2:
            print("Waiting for reconnection")
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': {
                    'message_type': MessageType.RECONNECT.value,
                    'message': 'Waiting for opponent to reconnect.',
                },
            })
            
    async def reconnect(self, event):
        game = cache.get(f'{self.game_id}_game')
        if not game:
            await self.channel_layer.group_send(self.group_name, {
                'type': MessageType.GAME_READY.value,
            })
            return
        bluePlayer = game.get_blue()
        redPlayer = game.get_red()
        blueName = cache.get(f'{self.game_id}_{bluePlayer}')['team_name']
        redName = cache.get(f'{self.game_id}_{redPlayer}')['team_name']
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index,
            'team': 'blue_team' if game.blue_team == self.cid else 'red_team',
            'blue_team': bluePlayer,
            'blue_team_name': blueName,
            'red_team': redPlayer,
            'red_team_name': redName,
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
        
    async def init_game(self, event):
        #get the user name from the message from "player_name"
        self.team_name = event.get('team_name')
        cache.set(f'{self.game_id}_{self.cid}', {
            'team_name': self.team_name,
        }, self.cache_timeout)
        
    async def game_ready(self, event):
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
                    'rule_set': self.rule_set,
                    'rule_set_selection': self.rule_set_selection
                }
            }
            await self.send_json(message)
    
    async def side_select(self, event):
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
        blueName = cache.get(f'{self.game_id}_{bluePlayer}')['team_name']
        redName = cache.get(f'{self.game_id}_{redPlayer}')['team_name']
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_START.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'blue_team': bluePlayer,
            'blue_team_name': blueName,
            'red_team': redPlayer,
            'red_team_name': redName,
        }
        message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
        }
        await self.channel_layer.group_send(self.group_name, message)
    
    async def reset_game(self, event):
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
        game = cache.get(f'{self.game_id}_game')
        bluePlayer = game.get_blue()
        redPlayer = game.get_red()
        blueName = cache.get(f'{self.game_id}_{bluePlayer}')['team_name']
        redName = cache.get(f'{self.game_id}_{redPlayer}')['team_name']
        game.undo_turn()
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index,
            'blue_team': bluePlayer,
            'blue_team_name': blueName,
            'red_team': redPlayer,
            'red_team_name': redName,
        }
        message = {
                'type': MessageType.FRONT_END_MESSAGE.value,
                'message': payload
        }
        await self.channel_layer.group_send(self.group_name, message)
    
    async def game_state(self, event):
        await self.send_json(event['message'])
        
    async def draft_ban(self, event):
        game = cache.get(f'{self.game_id}_game')
        bluePlayer = game.get_blue()
        redPlayer = game.get_red()
        blueName = cache.get(f'{self.game_id}_{bluePlayer}')['team_name']
        redName = cache.get(f'{self.game_id}_{redPlayer}')['team_name']
        res = game.update_state(event, 'ban')
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'success': res,
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index,
            'blue_team': bluePlayer,
            'blue_team_name': blueName,
            'red_team': redPlayer,
            'red_team_name': redName,
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.FRONT_END_MESSAGE.value, 'message': payload })
    
    async def draft_pick(self, event):
        game = cache.get(f'{self.game_id}_game')
        bluePlayer = game.get_blue()
        redPlayer = game.get_red()
        blueName = cache.get(f'{self.game_id}_{bluePlayer}')['team_name']
        redName = cache.get(f'{self.game_id}_{redPlayer}')['team_name']
        res = game.update_state(event, 'pick')
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'success': res,
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index,
            'blue_team': bluePlayer,
            'blue_team_name': blueName,
            'red_team': redPlayer,
            'red_team_name': redName,
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.FRONT_END_MESSAGE.value, 'message': payload })
    
    async def sig_eid_change(self, event):
        game = cache.get(f'{self.game_id}_game')
        game.sig_eid_change(event)
        bluePlayer = game.get_blue()
        redPlayer = game.get_red()
        blueName = cache.get(f'{self.game_id}_{bluePlayer}')['team_name']
        redName = cache.get(f'{self.game_id}_{redPlayer}')['team_name']
        cache.set(f'{self.game_id}_game', game, self.cache_timeout)
        payload = {
            'message_type': MessageType.GAME_STATE.value,
            'game_state': game.get_state(),
            'turn_player': game.get_turn_player(),
            'turn_index': game.turn_index,
            'blue_team': bluePlayer,
            'blue_team_name': blueName,
            'red_team': redPlayer,
            'red_team_name': redName,
        }
        await self.channel_layer.group_send(self.group_name, { 'type': MessageType.FRONT_END_MESSAGE.value, 'message': payload })
        
    async def front_end_message(self, event):
        print('received front end message')
        await self.send_json(event)



class SpectatorConsumer(GameConsumer):
    async def connect(self):
        # Called when the WebSocket is handshaking
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f'game_{self.game_id}'
        query_string = parse_qs(self.scope['query_string'].decode('utf8'))
        self.cid = query_string.get('cid')[0]
        if cache.get(f'{self.game_id}_rule_set'):
            self.rule_set = cache.get(f'{self.game_id}_rule_set')
        else:
            self.rule_set = query_string.get('ruleSet', ['phd_standard'])[0]
            print(self.rule_set)
            cache.set(f'{self.game_id}_rule_set', self.rule_set, self.cache_timeout)
        
        if cache.get(f'{self.game_id}_ruleSetSelection'):
            self.rule_set_selection = cache.get(f'{self.game_id}ruleSetSelection')
        else:
            self.rule_set_selection = query_string.get('ruleSetSelection', ['phd_standard'])[0]
            print(self.rule_set_selection)
            cache.set(f'{self.game_id}_ruleSetSelection', self.rule_set_selection, self.cache_timeout)
        # Accept the connection
        await self.accept()

        # Add this consumer to the game group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        # Called when the WebSocket closes
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        # Spectators cannot publish anything to the channel, so this method is empty
        pass
    
    async def front_end_message(self, event):
        # print('received front end message for spectators')
        await self.send_json(event)