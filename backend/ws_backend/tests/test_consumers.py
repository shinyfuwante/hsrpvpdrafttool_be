from channels.testing import ChannelsLiveServerTestCase
from channels.testing import WebsocketCommunicator
from ws_backend.routing import application
from ..internal.enums import MessageType
from django.core.cache import cache
from ..internal.draft_choices import Ban, Pick
import json
import os
import asyncio

class GameConsumerTests(ChannelsLiveServerTestCase):
    SERVER_URL = "ws/game/72e111a7-4c01-43bc-90eb-04b274949dfa?ruleSet=phd_standard&cid=abc12345"
    SERVER_URL_2 = "ws/game/72e111a7-4c01-43bc-90eb-04b274949dfa?ruleSet=phd_standard&cid=def67890"
    game_id = "72e111a7-4c01-43bc-90eb-04b274949dfa"
    
    def tearDown(self):
        cache.delete_many([f'{self.game_id}_selector', f'{self.game_id}_waiter', f'{self.game_id}_game', f'{self.game_id}_rule_set', f'{self.game_id}_characters', f'{self.game_id}_light_cones', f'{self.game_id}_connections', f'{self.game_id}_cids'])
                
    async def test_multiple_clients_connect_and_init_game(self):
        self.maxDiff = None
        # Create two WebSocket communicators that connect to the server
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL_2)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        assert connected1
        assert connected2
        res1 = await communicator1.receive_json_from()
        communicator1_cid = res1['message']['cid']
        res2 = await communicator2.receive_json_from()
        communicator2_cid = res2['message']['cid']
        selector = communicator1 if res1['message']['selector'] == communicator1_cid else communicator2
        waiter = communicator1 if not res1['message']['selector'] == communicator1_cid else communicator2
        
        side_select_message = ({
            'type': MessageType.SIDE_SELECT.value,
            'side': "blue" if selector == communicator1 else "red"
        })
        await selector.send_json_to(side_select_message)
        # when the selector selects their side, the game should finish initializing and the selector will be placed on their side
        # in this case, it is blue side
        res1 = await selector.receive_json_from()
        
        self.assertEqual(res1['message']['message_type'], MessageType.GAME_START.value)
        res2 = await waiter.receive_json_from()
        self.assertEqual(res2['message']['message_type'], MessageType.GAME_START.value)
        
        # we now play the game
        # selector will send a ban message, then waiter will send a ban message
        message = {
            'type': MessageType.BAN.value,
            'character': 'Arlan',
            'team': 'blue_team'
        }
        await selector.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message']['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['message']['game_state'].get('bans')
        self.assertEqual("Arlan" in game_state_bans['blue_team'], True)
        
        message = {
            'type': MessageType.BAN.value,
            'character': 'Herta',
            'team': 'red_team'
        }
        await waiter.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message']['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['message']['game_state'].get('bans')
        self.assertEqual("Herta" in game_state_bans['red_team'], True)
        # blue team picks Bronya E1S1 But the Battle Isn't Over
        bronya = {
            'name': 'Bronya',
            'eidolon': 1,
            'lightcone_name': 'But the Battle Isn\'t Over',
            'superimposition': 1,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': bronya
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Tingyun E0S0, Pela E0S0
        tingyun = {
            'name': 'Tingyun',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        pela = {
            'name': 'Pela',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': tingyun
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': pela
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        game_state = res['message']['game_state']
        self.assertEqual(game_state['picks']['blue_team'], [bronya])
        self.assertEqual(game_state['picks']['red_team'], [tingyun, pela])
        # blue team picks Yukong E0S5 Memories of the Past
        yukong = {
            'name': 'Yukong',
            'eidolon': 0,
            'lightcone_name': 'Memories of the Past',
            'superimposition': 5,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': yukong
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team bans Blade
        message = {
            'type': MessageType.BAN.value,
            'character': 'Blade',
            'team': 'red_team'
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team bans Dan Heng Imbibitor Lunae
        message = {
            'type': MessageType.BAN.value,
            'character': 'Dan Heng Imbibitor Lunae',
            'team': 'blue_team'
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Seele E0S1 In The Night
        seele = {
            'name': 'Seele',
            'eidolon': 0,
            'lightcone_name': 'In the Night',
            'superimposition': 1,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': seele,
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Fu Xuan E0S1 She Already Closed Her Eyes, Bailu E0S0
        fu_xuan = {
            'name': 'Fu Xuan',
            'eidolon': 0,
            'lightcone_name': 'She Already Closed Her Eyes',
            'superimposition': 1,
        }
        bailu = {
            'name': 'Bailu',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': fu_xuan
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': bailu
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Luocha, Huohuo
        luocha = {
            'name': 'Luocha',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        huohuo = {
            'name': 'Huohuo',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': luocha
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': huohuo
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Silver Wolf E0S5 Good Night and Sleep Well, Kafka E2S1 Patience is All You Need
        silver_wolf = {
            'name': 'Silver Wolf',
            'eidolon': 0,
            'lightcone_name': 'Good Night and Sleep Well',
            'superimposition': 5,
        }
        kafka = {
            'name': 'Kafka',
            'eidolon': 2,
            'lightcone_name': 'Patience is All You Need',
            'superimposition': 1,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': silver_wolf
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': kafka
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Jingliu E0S5 On the Fall of an Aeon, Asta E6S5 Meshing Cogs
        jingliu = {
            'name': 'Jingliu',
            'eidolon': 0,
            'lightcone_name': 'On the Fall of an Aeon',
            'superimposition': 5,
        }
        asta = {
            'name': 'Asta',
            'eidolon': 6,
            'lightcone_name': 'Meshing Cogs',
            'superimposition': 5,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': jingliu
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': asta
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        # blue team picks Clara E0S1 Something Irreplaceable, Topaz E0S1 Swordplay
        clara = {
            'name': 'Clara',
            'eidolon': 0,
            'lightcone_name': 'Something Irreplaceable',
            'superimposition': 1,
        }
        topaz = {
            'name': 'Topaz & Numby',
            'eidolon': 0,
            'lightcone_name': 'Swordplay',
            'superimposition': 1,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': clara
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': topaz
        }
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        # red team picks Sampo E6S5 Good Night and Sleep Well
        sampo = {
            'name': 'Sampo',
            'eidolon': 6,
            'lightcone_name': 'Good Night and Sleep Well',
            'superimposition': 5,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': sampo
        }
        await waiter.send_json_to(message)
        res = await selector.receive_json_from()
        game_state = res['message']['game_state']
        self.assertEquals(game_state['bans']['blue_team'], ['Arlan', 'Dan Heng Imbibitor Lunae'])
        self.assertEquals(game_state['bans']['red_team'], ['Herta', 'Blade'])
        self.assertEqual(game_state['picks']['blue_team'], [bronya, yukong, fu_xuan, bailu, silver_wolf, kafka, clara, topaz])
        self.assertEqual(game_state['picks']['red_team'], [tingyun, pela, seele, luocha, huohuo, jingliu, asta, sampo])
        await communicator1.disconnect()
        await communicator2.disconnect()
        
    async def test_clients_connect_and_disconnect(self):
        #repeat the ban and pick process up to blue pick 1
        self.maxDiff = None
        # Create two WebSocket communicators that connect to the server
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL_2)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        assert connected1
        assert connected2
        res1 = await communicator1.receive_json_from()
        communicator1_cid = res1['message']['cid']
        res2 = await communicator2.receive_json_from()
        communicator2_cid = res2['message']['cid']
        selector = communicator1 if res1['message']['selector'] == communicator1_cid else communicator2
        waiter = communicator1 if not res1['message']['selector'] == communicator1_cid else communicator2
        
        side_select_message = ({
            'type': MessageType.SIDE_SELECT.value,
            'side': "blue" if selector == communicator1 else "red"
        })
        await selector.send_json_to(side_select_message)
        # when the selector selects their side, the game should finish initializing and the selector will be placed on their side
        # in this case, it is blue side
        res1 = await selector.receive_json_from()
        
        self.assertEqual(res1['message']['message_type'], MessageType.GAME_START.value)
        res2 = await waiter.receive_json_from()
        self.assertEqual(res2['message']['message_type'], MessageType.GAME_START.value)
        
        # we now play the game
        # selector will send a ban message, then waiter will send a ban message
        message = {
            'type': MessageType.BAN.value,
            'character': 'Arlan',
            'team': 'blue_team'
        }
        await selector.send_json_to(message)
        res1 = await selector.receive_json_from()
        res2 = await waiter.receive_json_from()
        self.assertEqual(res1['message']['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['message']['game_state'].get('bans')
        self.assertEqual("Arlan" in game_state_bans['blue_team'], True)
        
        message = {
            'type': MessageType.BAN.value,
            'character': 'Herta',
            'team': 'red_team'
        }
        await waiter.send_json_to(message)
        res1 = await selector.receive_json_from()
        res2 = await waiter.receive_json_from()
        self.assertEqual(res1['message']['message_type'], MessageType.GAME_STATE.value)
        game_state_bans = res1['message']['game_state'].get('bans')
        self.assertEqual("Herta" in game_state_bans['red_team'], True)
        # blue team picks Bronya E1S1 But the Battle Isn't Over
        bronya = {
            'name': 'Bronya',
            'eidolon': 1,
            'lightcone_name': 'But the Battle Isn\'t Over',
            'superimposition': 1,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': bronya
        }
        
        await selector.send_json_to(message)
        res = await selector.receive_json_from()
        res = await waiter.receive_json_from()
        
        # disconnect one of the clients
        await communicator2.disconnect()
        await asyncio.sleep(1)
        res = await communicator1.receive_json_from()
        assert res['message']['message_type'] == MessageType.RECONNECT.value
        
        #reconnect
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL_2)
        await communicator2.connect()
        res = await communicator1.receive_json_from()
        self.assertEqual(res['message']['message_type'], MessageType.GAME_STATE.value)
        res = await communicator2.receive_json_from()
        self.assertEqual(res['message']['message_type'], MessageType.GAME_STATE.value)
        
        # red team picks Tingyun E0S0, Pela E0S0
        tingyun = {
            'name': 'Tingyun',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        pela = {
            'name': 'Pela',
            'eidolon': 0,
            'lightcone_name': '',
            'superimposition': 0,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': tingyun
        }
        await communicator2.send_json_to(message)
        res = await communicator1.receive_json_from()
        res = await communicator2.receive_json_from()
        message = {
            'type': MessageType.PICK.value,
            'team': 'red_team',
            'character': pela
        }
        await communicator2.send_json_to(message)
        res = await communicator1.receive_json_from()
        res = await communicator2.receive_json_from()
        game_state = res['message']['game_state']
        self.assertEqual(game_state['picks']['blue_team'], [bronya])
        self.assertEqual(game_state['picks']['red_team'], [tingyun, pela])
        
        # blue team picks Yukong E0S5 Memories of the Past
        yukong = {
            'name': 'Yukong',
            'eidolon': 0,
            'lightcone_name': 'Memories of the Past',
            'superimposition': 5,
        }
        message = {
            'type': MessageType.PICK.value,
            'team': 'blue_team',
            'character': yukong
        }
        await communicator1.send_json_to(message)
        res = await communicator1.receive_json_from()
        res = await communicator2.receive_json_from()
        # red team bans Blade
        message = {
            'type': MessageType.BAN.value,
            'character': 'Blade',
            'team': 'red_team'
        }
        await communicator2.send_json_to(message)
        res = await communicator1.receive_json_from()
        res = await communicator2.receive_json_from()
        
        # try disconnecting other client
        await communicator1.disconnect()
        await asyncio.sleep(2)
        
        print("trying to get reconnect message")
        res = await communicator2.receive_json_from()
        assert res['message']['message_type'] == MessageType.RECONNECT.value
        
        print("got reconnection message")
        
        #reconnect
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        await communicator1.connect()
        res = await communicator2.receive_json_from()
        self.assertEqual(res['message']['message_type'], MessageType.GAME_STATE.value)
        
        # disconnect communicator 2 and reconnect continuously until the team is not red_team
        # for _ in range(60):
        #     await communicator2.disconnect()
        #     await asyncio.sleep(1)
        #     communicator2 = WebsocketCommunicator(application, self.SERVER_URL_2)
        #     await communicator2.connect()
        #     res = await communicator2.receive_json_from()
        #     self.assertEqual(res['message']['message_type'], MessageType.GAME_STATE.value)
        #     self.assertEqual(res['message']['team'], "red_team")
            
        