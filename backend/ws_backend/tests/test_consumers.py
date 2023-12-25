from channels.testing import ChannelsLiveServerTestCase
from channels.testing import WebsocketCommunicator
from ws_backend.routing import application

class GameConsumerTests(ChannelsLiveServerTestCase):
    SERVER_URL = "ws/game/72e111a7-4c01-43bc-90eb-04b274949dfa"

    async def test_multiple_clients_can_connect_to_server(self):
        # Create two WebSocket communicators that connect to the server
        communicator1 = WebsocketCommunicator(application, self.SERVER_URL)
        communicator2 = WebsocketCommunicator(application, self.SERVER_URL)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)

        await communicator1.disconnect()
        await communicator2.disconnect()