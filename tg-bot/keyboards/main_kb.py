from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton("/moodle")
b2 = KeyboardButton("/shedule")
# b3 = KeyboardButton("/contacts")
# b4 = KeyboardButton("/complaint")

kb_main = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_main.row(b1, b2)

# .row(b3, b4)