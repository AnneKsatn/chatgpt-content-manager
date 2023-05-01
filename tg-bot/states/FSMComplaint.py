
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMComplaint(StatesGroup):
    complaint = State()