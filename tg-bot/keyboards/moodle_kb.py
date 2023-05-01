
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton("ошибка авторизации")
b2 = KeyboardButton("платформа недоступна")
b3 = KeyboardButton("меня не записали на курс")
b4 = KeyboardButton("отсутствует конференция в курсе")
b5 = KeyboardButton("предложить улучшения платформы")
b6 = KeyboardButton("отмена")

kb_moodle = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_moodle.add(b1).add(b2).add(b3).add(b4).add(b5).add(b6)
