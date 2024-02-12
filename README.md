# Websocket Backend for Star Rail Pick ban
https://starrailpb.dev/

This is the repo for a back end component designed to provide real-time communication functionality using Django Channels, Daphne, Redis, and Websockets. 

* The core of this backend is built on Django Channels (an extension of the Django web framework for Python) to handle the Websocket connections to allow for bidirectional communications in a full-duplex communication system.
* Daphne is used as the ASGI Server to run the Django Channels application and provides the infrastructure to handle asynchronous tasks.
* Redis is the channel layer and acts as the messaging system where users can subscribe to the channel group and messages that are published from one user are propagated amongst the other users. This allows for changes in game state to reach both players as well as provide a way for players to select their side and make their draft picks. Because the pub/sub model is implemented through Redis, this should allow for scalability of a game, if desired.

This back end is currently hosted on Railway, but does have a docker-compose file with NGINX set as the reverse proxy for scalability in the future, if there is a need to handle more users. 
