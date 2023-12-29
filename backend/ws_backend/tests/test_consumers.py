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
        self.maxDiff = None
        # Create two WebSocket communicators that connect to the server
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        assert connected1
        assert connected2
        res1 = await communicator1.receive_json_from()
        communicator1_cid = res1['cid']
        res2 = await communicator2.receive_json_from()
        communicator2_cid = res2['cid']
        selector = communicator1 if res1['selector'] == communicator1_cid else communicator2
        waiter = communicator1 if not res1['selector'] == communicator1_cid else communicator2
        
        side_select_message = ({
            'type': MessageType.SIDE_SELECT.value,
            'side': "blue" if selector == communicator1 else "red"
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
        arlan_ban = {
            'name': 'Arlan',
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': arlan_ban
        }
        await selector.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['game_state'].get('bans')
        self.assertEqual(arlan_ban in game_state_bans['blue_team'], True)
        herta_ban = {
            'name': 'Herta',
            'team': 'red_team'
        }
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': herta_ban
        }
        await waiter.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['game_state'].get('bans')
        self.assertEqual(herta_ban in game_state_bans['red_team'], True)
        # blue team picks Bronya E1S1 But the Battle Isn't Over
        bronya = {
            'name': 'Bronya',
            'eidolon': 1,
            'lightcone_name': 'But the Battle Isn\'t Over',
            'superimposition': 1,
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': bronya
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Tingyun E0S0, Pela E0S0
        tingyun = {
            'name': 'Tingyun',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
            'team': 'red_team'
        }
        pela = {
            'name': 'Pela',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
            'team': 'red_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': tingyun
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': pela
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        game_state = res['game_state']
        self.assertEqual(game_state['picks']['blue_team'], [bronya])
        self.assertEqual(game_state['picks']['red_team'], [tingyun, pela])
        # blue team picks Yukong E0S5 Memories of the Past
        yukong = {
            'name': 'Yukong',
            'eidolon': 0,
            'lightcone_name': 'Memories of the Past',
            'superimposition': 5,
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': yukong
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team bans Blade
        blade_ban = {
            'name': 'Blade',
            'team': 'red_team'
        }
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': blade_ban
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team bans Dan Heng Imbibitor Lunae
        dhil_ban = {
            'name': 'Dan Heng Imbibitor Lunae',
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': dhil_ban
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Seele E0S1 In The Night
        seele = {
            'name': 'Seele',
            'eidolon': 0,
            'lightcone_name': 'In the Night',
            'superimposition': 1,
            'team': 'red_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': seele,
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Fu Xuan E0S1 She Already Closed Her Eyes, Bailu E0S0
        fu_xuan = {
            'name': 'Fu Xuan',
            'eidolon': 0,
            'lightcone_name': 'She Already Closed Her Eyes',
            'superimposition': 1,
            'team': 'blue_team'
        }
        bailu = {
            'name': 'Bailu',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': fu_xuan
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': bailu
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Luocha, Huohuo
        luocha = {
            'name': 'Luocha',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
            'team': 'red_team'
        }
        huohuo = {
            'name': 'Huohuo',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
            'team': 'red_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': luocha
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': huohuo
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Silver Wolf E0S5 Good Night and Sleep Well, Kafka E2S1 Patience is All You Need
        silver_wolf = {
            'name': 'Silver Wolf',
            'eidolon': 0,
            'lightcone_name': 'Good Night and Sleep Well',
            'superimposition': 5,
            'team': 'blue_team'
        }
        kafka = {
            'name': 'Kafka',
            'eidolon': 2,
            'lightcone_name': 'Patience is All You Need',
            'superimposition': 1,
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': silver_wolf
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': kafka
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Jingliu E0S5 On the Fall of an Aeon, Asta E6S5 Meshing Cogs
        jingliu = {
            'name': 'Jingliu',
            'eidolon': 0,
            'lightcone_name': 'On the Fall of an Aeon',
            'superimposition': 5,
            'team': 'red_team'
        }
        asta = {
            'name': 'Asta',
            'eidolon': 6,
            'lightcone_name': 'Meshing Cogs',
            'superimposition': 5,
            'team': 'red_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': jingliu
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': asta
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Clara E0S1 Something Irreplaceable, Topaz E0S1 Swordplay
        clara = {
            'name': 'Clara',
            'eidolon': 0,
            'lightcone_name': 'Something Irreplaceable',
            'superimposition': 1,
            'team': 'blue_team'
        }
        topaz = {
            'name': 'Topaz & Numby',
            'eidolon': 0,
            'lightcone_name': 'Swordplay',
            'superimposition': 1,
            'team': 'blue_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': clara
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': topaz
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Sampo E6S5 Good Night and Sleep Well
        sampo = {
            'name': 'Sampo',
            'eidolon': 6,
            'lightcone_name': 'Good Night and Sleep Well',
            'superimposition': 5,
            'team': 'red_team'
        }
        message = {
            'type': MessageType.PICK.value,
            'message_type': MessageType.PICK.value,
            'pick': sampo
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        game_state = res['game_state']
        self.assertEquals(game_state['bans']['blue_team'], [arlan_ban, dhil_ban])
        self.assertEquals(game_state['bans']['red_team'], [herta_ban, blade_ban])
        self.assertEqual(game_state['picks']['blue_team'], [bronya, yukong, fu_xuan, bailu, silver_wolf, kafka, clara, topaz])
        self.assertEqual(game_state['picks']['red_team'], [tingyun, pela, seele, luocha, huohuo, jingliu, asta, sampo])
        await communicator1.disconnect()
        await communicator2.disconnect()