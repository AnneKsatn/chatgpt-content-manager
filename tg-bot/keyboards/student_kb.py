from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

b1 = InlineKeyboardButton(text="расписание", callback_data="shedule")
b2 = InlineKeyboardButton(text="moodle", callback_data="moodle")
b3 = InlineKeyboardButton(text="оставить жалобу", callback_data="complaint")

# b4 = KeyboardButton("/documents")
# b5 = KeyboardButton("/diploma")

kb_student = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_student.add(b1).add(b2).add(b3)