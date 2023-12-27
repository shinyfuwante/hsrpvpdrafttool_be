from channels.testing import ChannelsLiveServerTestCase
from channels.testing import WebsocketCommunicator
from ws_backend.routing import application
from ..internal.enums import MessageType
from django.core.cache import cache
from ..internal.draft_choices import Ban, Pick
import json

# Load the JSON data from a file
with open('../internal.characters.json', 'r') as f:
    characters = json.load(f)


# Load the JSON data from a file
with open('../internal/light_cones.json', 'r') as f:
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
            'ban': characters['Arlan']
        }
        await selector.send_json_to(message)
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.GAME_STATE.value)
        res2 = await waiter.receive_json_from()
        self.assertEqual(res2['message_type'], MessageType.GAME_STATE.value)
        message = {
            'type': MessageType.BAN.value,
            'message_type': MessageType.BAN.value,
            'ban': characters['Herta']
        }
        res1 = await selector.receive_json_from()
        self.assertEqual(res1['message_type'], MessageType.GAME_STATE.value)
        res2 = await waiter.receive_json_from()
        self.assertEqual(res2['message_type'], MessageType.GAME_STATE.value)
        await communicator1.disconnect()
        await communicator2.disconnect()