# Websocket Backend for Honkai: Star Rail Pick Ban
https://starrailpb.dev/

This is the repo for a back end component designed to provide real-time communication functionality using Django Channels, Daphne, Redis, and Websockets to handle the lobbies made for https://starrailpb.dev/.

* The core of this backend is built on Django Channels (an extension of the Django web framework for Python) to handle the Websocket connections to allow for bidirectional communications in a full-duplex communication system.
* Daphne is used as the ASGI Server to run the Django Channels application and provides the infrastructure to handle asynchronous tasks.
* Redis is the channel layer and acts as the messaging system where users can subscribe to the channel group and messages that are published from one user are propagated amongst the other users. This allows for changes in game state to reach both players as well as provide a way for players to select their side and make their draft picks. Because the pub/sub model is implemented through Redis, this should allow for scalability of a game, if desired.

This back end is currently hosted on Railway, but does have a docker-compose file with NGINX set as the reverse proxy for scalability in the future, if there is a need to handle more users. 

I chose Django Channels to handle my websocket back end to get better at the high level understanding of multi-client communication. 

The use of a GameConsumer provided by Django Channels helps to route messages to and from the front end component. There are defined message types (game_start, side_selection, game_state, etc) that can be sent to the front end component to handle the payload. This back end component is in charge of receiving and routing the messages to the correct locations, as well as interface with the Redis cache that holds information about the game state, players, and more. This cache cleans itself up when both players disconnect or after 3 hours of inactivity. 

A Redis cache was selected for this task because these game states are ultimately temporary. Any record of these games are stored using the Discord server's Player vs Player bot. Redis was chosen due to its fast read and writes due to being an in-memory data store and its built in support for Pub/Sub messaging, as well as being easily scalable.

A test was made to be exercised using Github workflows to provide sanity as I made changes to the back end. This gave me the confidence to move fast and to also revisit the back end if I need to.
