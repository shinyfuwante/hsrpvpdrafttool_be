from channels.testing import ChannelsLiveServerTestCase
from channels.testing import WebsocketCommunicator
from ws_backend.routing import application
from ..internal.enums import MessageType
from django.core.cache import cache
import asyncio

class GameConsumerTests(ChannelsLiveServerTestCase):
    SERVER_URL = "ws/game/72e111a7-4c01-43bc-90eb-04b274949dfa"
    
    def tearDown(self):
        cache.delete('72e111a7-4c01-43bc-90eb-04b274949dfa')
        
    async def test_multiple_clients_connect_and_init_game(self):
        # Create two WebSocket communicators that connect to the server
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)
        
        # creator will send an init message to the server
        message = {
            'type': MessageType.INIT_GAME.value,
            'message_type': MessageType.INIT_GAME.value,
        }
        await communicator1.send_json_to(message)
        await asyncio.sleep(2)
        response1 = await communicator1.receive_from()
        print("Received response1")
        response2 = await communicator2.receive_from(2)
        self.assertEqual(response1['message_type'], MessageType.SIDE_SELECT.value or MessageType.SIDE_SELECT_WAITER.value)
        self.assertEqual(response2['message_type'], MessageType.SIDE_SELECT.value or MessageType.SIDE_SELECT_WAITER.value)
        
        await communicator1.disconnect()
        await communicator2.disconnect()