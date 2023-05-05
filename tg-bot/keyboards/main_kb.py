from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton("/generate_content_plan")
b2 = KeyboardButton("/generate_post")
# b3 = KeyboardButton("/contacts")
# b4 = KeyboardButton("/complaint")

kb_main = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_main.row(b1, b2)

# .row(b3, b4)