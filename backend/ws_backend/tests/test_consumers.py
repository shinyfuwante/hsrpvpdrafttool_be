from channels.testing import ChannelsLiveServerTestCase
from channels.testing import WebsocketCommunicator
from ws_backend.routing import application
from ..internal.enums import MessageType
from django.core.cache import cache
from ..internal.draft_choices import Ban, Pick
import json
import os
import asyncio

print(os.getcwd())
with open('./ws_backend/internal/characters.json', 'r') as f:
    characters = json.load(f)
    

with open('./ws_backend/internal/light_cones.json', 'r') as f:
    light_cones = json.load(f)

class GameConsumerTests(ChannelsLiveServerTestCase):
    SERVER_URL = "ws/game/72e111a7-4c01-43bc-90eb-04b274949dfa"
    game_id = "72e111a7-4c01-43bc-90eb-04b274949dfa"
    
    def tearDown(self):
        cache.delete(self.game_id)
        
    async def test_multiple_clients_connect_and_init_game(self):
        # Create two WebSocket communicators that connect to the server
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        assert connected1
        assert connected2
        # creator will send an init message to the server
        message = {
            'type': MessageType.INIT_GAME.value,
            'message_type': MessageType.INIT_GAME.value,
        }
        await communicator1.send_json_to(message)
        res1 = await communicator1.receive_json_from()
        res2 = await communicator2.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.SIDE_SELECT.value or MessageType.SIDE_SELECT_WAITER.value)
        self.assertEqual(res2['message_type'], MessageType.SIDE_SELECT.value or MessageType.SIDE_SELECT_WAITER.value)
        selector = communicator1 if res1['message_type'] == MessageType.SIDE_SELECT.value else communicator2
        waiter = communicator1 if res1['message_type'] == MessageType.SIDE_SELECT_WAITER.value else communicator2
        
        side_select_message = ({
            'type': MessageType.SIDE_SELECT.value,
            'side': 0 if selector == communicator1 else 1
        })
        await selector.send_json_to(side_select_message)
        # when the selector selects their side, the game should finish initializing and the selector will be placed on their side
        # in this case, it is blue side
        res1 = await selector.receive_json_from()
        
        self.assertEqual(res1['message_type'], MessageType.GAME_START.value)
        res2 = await waiter.receive_json_from()
        self.assertEqual(res2['message_type'], MessageType.GAME_START.value)
        
        # we now play the game
        # selector will send a ban message, then waiter will send a ban message
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': 'Arlan'
        }
        await selector.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['game_state'].get('bans')
        self.assertEqual('Arlan' in game_state_bans['blue_team'], True)
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': 'Herta'
        }
        await waiter.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['game_state'].get('bans')
        self.assertEqual('Herta' in game_state_bans['red_team'], True)
        # blue team picks Bronya
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Bronya'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Tingyun, Pela
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Tingyun'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Pela'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        game_state = res['game_state']
        self.assertEqual(game_state['picks']['blue_team'], ['Bronya'])
        self.assertEqual(game_state['picks']['red_team'], ['Tingyun', 'Pela'])
        # blue team picks Yukong
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Yukong'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team bans Blade
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': 'Blade'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team bans Dan Heng Imbibitor Lunae
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': 'Dan Heng Imbibitor Lunae'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Seele
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Seele'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Fu Xuan, Bailu
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Fu Xuan'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Bailu'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Luocha, Huohuo
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Luocha'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Huohuo'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Silver Wolf, Kafka
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Silver Wolf'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Kafka'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Jingliu, Asta
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Jingliu'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Asta'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Clara, Topaz
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Clara'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Topaz'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Sampo
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': 'Sampo'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        game_state = res['game_state']
        self.assertEqual(game_state['picks']['blue_team'], ['Bronya', 'Yukong', 'Fu Xuan', 'Bailu', 'Silver Wolf', 'Kafka', 'Clara', 'Topaz'])
        self.assertEqual(game_state['picks']['red_team'], ['Tingyun', 'Pela', 'Seele', 'Luocha', 'Huohuo', 'Jingliu', 'Asta', 'Sampo'])
        
        await communicator1.disconnect()
        await communicator2.disconnect()