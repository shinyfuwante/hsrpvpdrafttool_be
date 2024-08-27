from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from ws_backend import consumers

websocket_urlpatterns = [
    path('ws/game/<uuid:game_id>', consumers.GameConsumer.as_asgi()),
    path('ws/watch/<uuid:game_id>', consumers.SpectatorConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns),
})