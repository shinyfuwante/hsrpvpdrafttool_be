from enum import Enum

class MessageType(Enum):
    INIT_GAME = 'init_game'
    GAME_READY = 'game_ready'
    GAME_START = 'game_start'
    GAME_STATE = 'game_state'
    SIDE_SELECT = "side_select"
    SIDE_SELECT_WAITER = "side_select_waiter"
    FRONT_END_MESSAGE = 'front_end_message'
    BAN = "draft_ban"
    PICK = "draft_pick"
    UNDO = "undo"
    RESET_GAME = "reset_game"
    RECONNECT = "reconnect"
    ERROR = "error"
    
class ErrorType(Enum):
    FULL_GAME = "full_game"
    SAME_CONNECTION = "same_connection"
    