import os
import pprint

import data_fetcher
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from linkedin_api import Linkedin
from local_settings import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
from requests_oauthlib import OAuth2Session

scope = ["r_liteprofile"]
redirect_url = "https://localhost:8432/token?chat_id={}"
authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
token_url = "https://www.linkedin.com/oauth/v2/accessToken"
linkedin = lambda chat_id: OAuth2Session(LINKEDIN_CLIENT_ID, redirect_uri=redirect_url.format(chat_id), scope=scope)


storage = MemoryStorage()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot, storage=storage)

##################### АВТОРИАЗАЦИЯ ########################


@dp.message_handler(commands="start")
async def command_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Linkedin аутентификация")
    keyboard.add(button_phone)

    await bot.send_message(
        message.chat.id,
        "Привет! Рад тебя видеть!\n\n"
        "Пожалуйста, предоставь доступ к своему Linkedin, чтобы я мог составить план контента.",
        reply_markup=keyboard,
    )


@dp.message_handler(Text(startswith="Linkedin аутентификация"))
async def contact(message):
    authorization_url, state = linkedin(message.chat.id).authorization_url(authorization_base_url)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="Готово!"))

    await bot.send_message(
        message.chat.id,
        f"Для авторизации подтвердите доступ для приложения: {authorization_url}",
        reply_markup=keyboard,
    )


@dp.message_handler(Text(startswith="Готово"))
async def check_profile(message: types.Message, state: FSMContext):
    user_info = await data_fetcher.get_info(message.chat.id)
    print(user_info)


@dp.message_handler(commands="generate_content_plan")
async def command_start(message: types.Message):
    content_plan = await data_fetcher.generate_content_plan(message.chat.id)
    await bot.send_message(message.chat.id, "Контент-план: \n" + content_plan)


##################### ГЛАВНЫЙ МАКЕТ ########################

# @dp.message_handler(commands='help')
# async def command_start(message: types.Message):
#     await message.answer("Чем я могу помочь?", reply_markup=kb_main)

##################### ГЛАВНЫЙ МАКЕТ: MOODLE ########################

# @dp.message_handler(commands='moodle')
# async def professors(message: types.Message):
#     await message.answer("Чем я могу помочь?", reply_markup=kb_moodle)

# @dp.message_handler(Text(startswith='ошибка авторизации'))
# async def professors(message: types.Message):

#     admins = await data_fetcher.get_admins()
#     user = await data_fetcher.get_user_by_chat(message.chat.id)

#     print(user)
#     for admin in admins:
#         await bot.send_message(
#             admin['chat_id'],
#             "Ошибка авторизации на платформе у пользователя \n" + user['name'] + " " + user['phone']
#             )

#     await message.answer(
#         "Специалисты проверят в течение часа - двух и сбросят пароль на исходный: 123456a* (a печатается латинским шрифтом). Если доступ к платформе нужно получить срочно, напиши куратору группы.",
#         reply_markup=kb_main)

# @dp.message_handler(Text(startswith='платформа недоступна'))
# async def professors(message: types.Message):

#     admins = await data_fetcher.get_admins()
#     user = await data_fetcher.get_user_by_chat(message.chat.id)

#     for admin in admins:
#         await bot.send_message(
#             admin['chat_id'],
#             "Платформа недоступна у пользоавателя \n" + user['name'] + " " + user['phone']
#             )

#     await message.answer(
#         "Передал специалисту ошибку, платформу уже восстанавливают. Если у тебя сейчас занятие, попробуй договриться с преподавателем провести занятие на другом ресурсе (zoom, meets и т.д)",
#         reply_markup=kb_main)


##################### ГЛАВНЫЙ МАКЕТ: РАСПИСАНИЕ ########################

# @dp.message_handler(commands=['shedule'])
# async def url_command(message: types.Message):

#     res = await data_fetcher.get_shedule()
#     week_days = {1: "Понедельник", 2: "Вторник",3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}

#     message_text="Расписание:\n"
#     current_day = -1

#     for course in res:
#         if(course['week_day'] > current_day):

#             current_day = course['week_day']
#             message_text = message_text + "\n<b><u>" + week_days[current_day] + "</u></b>\n\n"

#         message_text = message_text + course["title"] + "\n" + course["day_time"] + " " + course["teacher"] + "\n\n"


#     await bot.send_message(
#         message.chat.id,
#         text = message_text,
#         parse_mode=ParseMode.HTML
#     )


##################### Обработка жалоб ########################

# @dp.message_handler(commands='complaint', state=None)
# async def professors(message: types.Message):

#     await FSMComplaint.complaint.set()
#     await message.reply('Опиши свою жалобу одним сообщением и я передам ее администрации')


# @dp.message_handler(state=FSMComplaint.complaint)
# async def mark_lecture(message: types.Message, state: FSMContext):
#     async with state.proxy() as data:
#         data['complaint'] = message.text
#         await message.reply("Спасибо за обратную связь! Я передам в администрацию следующую жалобу: \n\n" + message.text)

#     await state.finish()


##################### СБОР ФИДБЕКА О ОНЛАЙН-ЛЕКТОРИИ ########################

# def create_markup(lesson_id):
#     lecture_marks_markup = InlineKeyboardMarkup(row_width=5).add(
#         InlineKeyboardButton(text="10", callback_data="lecture_mark_10_" + lesson_id),
#         InlineKeyboardButton(text="9", callback_data="lecture_mark_9_" + lesson_id),
#         InlineKeyboardButton(text="8", callback_data="lecture_mark_8_" + lesson_id),
#         InlineKeyboardButton(text="7", callback_data="lecture_mark_7_" + lesson_id),
#         InlineKeyboardButton(text="6", callback_data="lecture_mark_6_" + lesson_id),
#         InlineKeyboardButton(text="5", callback_data="lecture_mark_5_" + lesson_id),
#         InlineKeyboardButton(text="4", callback_data="lecture_mark_4_" + lesson_id),
#         InlineKeyboardButton(text="3", callback_data="lecture_mark_3_" + lesson_id),
#         InlineKeyboardButton(text="2", callback_data="lecture_mark_2_" + lesson_id),
#         InlineKeyboardButton(text="1", callback_data="lecture_mark_1_" + lesson_id))
#     return lecture_marks_markup


# @dp.callback_query_handler(Text(startswith='lecture_mark'))
# async def mark_lecture(callback: types.CallbackQuery):
#     res = int(callback.data.split('_')[2])
#     lesson_id = callback.data.split('_')[3]


# async def get_lectures_feedback(user, course):

#         lesson = data_fetcher.get_lesson()

#         if lesson['asynchronous_lectures']:

#             text = 'К данному уроку нужно было пройти материал: \n\n'

#             for lecture in lesson['asynchronous_lectures']:
#                 text = text + lecture + "\n"


#             await bot.send_message(
#                 user['chat_id'],
#                 text + "\n Помоги нам оценить качество и улучшить курс :)")

#             await bot.send_message(
#                 user['chat_id'],
#                 'Оцени по 10-бальной шкале полезность лекции',
#                 reply_markup=create_markup(lesson['_id']))

#             await bot.send_message(
#                 user['chat_id'],
#                 'Оцени по 10-бальной шкале качество объяснения материала и понятность лекции',
#                 reply_markup=create_markup(lesson['_id']))


##################### ОТПРАВЛЕНИЕ НАПОМИНАНИЙ О ПАРАХ ########################


# async def print_reminder(course):

#     users = await data_fetcher.get_students()

#     for user in users:
#         await bot.send_message(user["chat_id"], "Привет! Через 10 минут у тебя будет пара на курсе " + course['title'])

#     if course['asynchronous_content']:
#         get_lectures_feedback(user, course)


# async def reminder_scheduler():

#     courses = await data_fetcher.get_courses()
#     courses = [{"teacher":"Муравьев Сергей Борисович","title":"Deep Learning","week_day":2,"day_time":"21:35"}]

#     for course in courses:
#         print(course)

#         minutes = int(course['day_time'][3:5]) - 10
#         hours = int(course['day_time'][0:2])

#         shedule_time = str(hours) + ":" + str(minutes)

#         if course['week_day'] == 1:
#             aioschedule.every().monday.at(shedule_time).do(print_reminder)

#         if course['week_day'] == 2:
#             aioschedule.every().tuesday.at(shedule_time).do(print_reminder, course)

#         if course['week_day'] == 3:
#             aioschedule.every().wednesday.at(shedule_time).do(print_reminder, course)

#         if course['week_day'] == 4:
#             aioschedule.every().thursday.at(shedule_time).do(print_reminder, course)

#         if course['week_day'] == 5:
#             aioschedule.every().friday.at(shedule_time).do(print_reminder, course)

#         if course['week_day'] == 6:
#             aioschedule.every().saturday.at(shedule_time).do(print_reminder, course)


#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(1)

##################### СБОР ФИДБЕКА ########################

# async def ask_lesson_feedback():

#     for chat in users:
#         await bot.send_message(chat,
#         "Привет! Сегодня ты прошел темы: \n Математическая модель нейрона \n Однослойный перцепторн \n Многослойный перцептрон. Оцени, пожалуйста, занятие:", reply_markup=marks_markup)


# async def lesson_feedback_scheduler():
#     # courses = get_random()

#     courses = [{"teacher":"Муравьев Сергей Борисович","title":"Deep Learning","week_day":2,"day_time":"21:35"}]

#     for course in courses:
#         print(course)
#         minutes = int(course['day_time'][3:5]) + 30
#         hours = int(course['day_time'][0:2])

#         if(minutes > 60):
#             hours = hours + 1
#             minutes = minutes + 30 - 60

#         lesson_time = str(hours) + ":" + str(minutes)

#         print(course['day_time'][0:3] + str(minutes))

#         if course['week_day'] == 1:
#             aioschedule.every().monday.at(lesson_time).do(ask_lesson_feedback)

#         if course['week_day'] == 2:
#             aioschedule.every().tuesday.at(lesson_time).do(ask_lesson_feedback, course['title'])

#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(1)


async def on_startup(_):
    print("Bot started")
    # asyncio.create_task(reminder_scheduler())
    # asyncio.create_task(lesson_feedback_scheduler())


# marks_markup = InlineKeyboardMarkup(row_width=5).add(
#     InlineKeyboardButton(text="10", callback_data="mark_10"),
#     InlineKeyboardButton(text="9", callback_data="mark_9"),
#     InlineKeyboardButton(text="8", callback_data="mark_8"),
#     InlineKeyboardButton(text="7", callback_data="mark_7"),
#     InlineKeyboardButton(text="6", callback_data="mark_6"),
#     InlineKeyboardButton(text="5", callback_data="mark_5"),
#     InlineKeyboardButton(text="4", callback_data="mark_4"),
#     InlineKeyboardButton(text="3", callback_data="mark_3"),
#     InlineKeyboardButton(text="2", callback_data="mark_2"),
#     InlineKeyboardButton(text="1", callback_data="mark_1"))


# @dp.callback_query_handler(Text(startswith='mark_'))
# async def mark_lecture(callback: types.CallbackQuery):
#     res = int(callback.data.split('_')[1])
#     if f'{callback.from_user.id}' not in answ:
#         answ[f'{callback.from_user.id}'] = res
#         await callback.message("Спасибо! Твой отзыв очень важен для обучения будущих потоков :)")
#     else:
#         await callback.answer("Ты уже проголосовал :)", show_alert=True)


executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
