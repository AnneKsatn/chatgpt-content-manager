
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMPlatformFeedback(StatesGroup):
    getting_feedback = State()