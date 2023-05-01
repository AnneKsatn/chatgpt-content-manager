
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMStudentLogin(StatesGroup):
    login = State()
    password = State()