

from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMEnrollmentError(StatesGroup):
    course_title = State()