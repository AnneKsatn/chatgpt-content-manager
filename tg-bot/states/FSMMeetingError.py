
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMMeetingError(StatesGroup):
    course_title = State()