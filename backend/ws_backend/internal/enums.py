from enum import Enum

class MessageType(Enum):
    INIT_GAME = 'init_game'
    GAME_START = 'game_start'
    GAME_STATE = 'game_state'
    SIDE_SELECT = "side_select"
    SIDE_SELECT_WAITER = "side_select_waiter"
    FRONT_END_MESSAGE = 'front_end_message'
    BAN = "draft_ban"