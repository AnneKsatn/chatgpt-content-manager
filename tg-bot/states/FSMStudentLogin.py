
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMLinkedinLogin(StatesGroup):
    login = State()
    password = State()