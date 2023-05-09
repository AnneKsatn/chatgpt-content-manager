import logging
import os
import re

import data_fetcher
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from data_fetcher import HandledError
from local_settings import LINKEDIN_CLIENT_ID
from requests_oauthlib import OAuth2Session
from texts import translations

scope = ["r_liteprofile", "w_member_social"]
redirect_url = "https://localhost:8432/token?chat_id={}"
authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
token_url = "https://www.linkedin.com/oauth/v2/accessToken"
linkedin = lambda chat_id: OAuth2Session(LINKEDIN_CLIENT_ID, redirect_uri=redirect_url.format(chat_id), scope=scope)
ACCOUNT_REGEXP = r'((http(s)?:\/\/)?(www\.)?linkedin\.com\/in\/)?([A-Za-z0-9_.-]+)(/)?'

storage = MemoryStorage()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot, storage=storage)

# the on_throttled object can be either a regular function or coroutine
async def throttled(*args, **kwargs):
    message = args[0]  # as message was the first argument in the original handler
    await message.reply("Throttled, once per 5 mins")


# States
class Form(StatesGroup):
    account = State()
    check_account = State()
    gen_plan = State()


async def error_handler(mess, err_mess):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text=translations.generate_plan_cmd))
    await mess.reply(err_mess, reply_markup=keyboard)


##################### АВТОРИАЗАЦИЯ ########################


@dp.message_handler(commands=translations.start_cmd[1:])
async def command_start(message: types.Message):
    await Form.account.set()
    await bot.send_message(
        message.chat.id,
        translations.start_message
    )


@dp.message_handler(state=Form.account)
async def get_account(message: types.Message, state: FSMContext):
    logging.info(message)
    parsed = re.search(ACCOUNT_REGEXP, message.text)
    account_id = parsed.group(5)
    user_info = await data_fetcher.get_info(message.chat.id, account_id)

    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text=translations.approve_message))
    keyboard.add(types.KeyboardButton(text=translations.deny_message))
    print(user_info)
    await Form.next()
    await bot.send_message(message.chat.id,
                           translations.hello_message.format(fullName=user_info['fullName']),
                           reply_markup=keyboard)


@dp.message_handler(state=Form.check_account)
async def check_account(message: types.Message, state: FSMContext):
    if 'no' in message.text.lower():
        await Form.account.set()
        await bot.send_message(message.chat.id, translations.link_again)
        return

    await Form.next()
    await gen_plan()


@dp.message_handler(state=Form.gen_plan)
@dp.message_handler(commands=[translations.generate_plan_cmd[1:]])
@dp.throttled(throttled, rate=300)
@dp.errors_handler(exception=HandledError, run_task=lambda message: error_handler(message, 'There was a problem during your request :('))
async def gen_plan(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_gen_post = types.KeyboardButton(text=translations.generate_post)
    keyboard.add(button_gen_post)

    can_generate, plan = await data_fetcher.can_generate_plan(message.chat.id)
    if not can_generate:
        await bot.send_message(message.chat.id,
                               translations.generation_error.format(plan=plan))
    else:
        await bot.send_message(message.chat.id, translations.content_plan_generated)
        await state.finish()
        content_plan = await data_fetcher.generate_content_plan(message.chat.id)
        await bot.send_message(message.chat.id,
                               translations.content_plan_created.format(response=content_plan['response']))

    await bot.send_message(message.chat.id,
                           translations.offer_generate_post,
                           reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith(translations.generate_post) or message.text.startswith(translations.next_post))
@dp.throttled(throttled, rate=300)
@dp.errors_handler(exception=HandledError, run_task=lambda message: error_handler(message, 'There was a problem during your request :('))
async def next_post(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, translations.wait_for_post)

    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_post = types.KeyboardButton(text=translations.next_post)
    keyboard.add(button_post)
    button_publish = types.KeyboardButton(text=translations.publish)
    keyboard.add(button_publish)

    post = await data_fetcher.generate_next_post(message.chat.id)
    if post.get('error', None) or not 'response' in post:
        newposts_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        newposts_keyboard.add(types.KeyboardButton(text=translations.generate_plan_cmd))
        newposts_keyboard.add(types.KeyboardButton(text=translations.generate_post))
        await bot.send_message(message.chat.id,
                               translations.generate_new_posts,
                               reply_markup=newposts_keyboard)
    else:
        topic = post.get('meta', {}).get('heading', '')
        if imgs := post.get('images', []):
            # Create media group
            media = types.MediaGroup()

            # You can also use URL's
            # For example: get random puss:
            for img in imgs:
                media.attach_photo(img, topic)

            # Done! Send media group
            if imgs:
                await message.reply_media_group(media=media)
        await bot.send_message(message.chat.id,
                               f"{topic}\n{post['response']}",
                               reply_markup=keyboard)


@dp.message_handler(commands=[translations.check_auth[1:], translations.publish[1:]])
@dp.errors_handler(exception=HandledError, run_task=lambda message: error_handler(message, 'There was a problem during your request :('))
async def publish_post(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, translations.access_checking)
    is_auth = await data_fetcher.check_auth(message.chat.id)
    if not is_auth['is_auth']:
        await bot.send_message(message.chat.id, translations.publish_precaution)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_auth = types.KeyboardButton(text=translations.check_auth)
        keyboard.add(button_auth)
        authorization_url, state = linkedin(message.chat.id).authorization_url(authorization_base_url)
        await bot.send_message(message.chat.id,
                               translations.provide_access.format(authorization_url=authorization_url),
                               reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button_post = types.KeyboardButton(text=translations.next_post)
        keyboard.add(button_post)
        is_posted = await data_fetcher.publish_post(message.chat.id)
        await bot.send_message(message.chat.id,
                               translations.published if is_posted else translations.failed_publish,
                               reply_markup=keyboard)


class GenArt(StatesGroup):
    gen = State()


@dp.message_handler(commands=['generate_art_prompt'])
async def gen_art_prompt(message):
    await GenArt.gen.set()
    await message.reply('Send your publication text prompt')


@dp.message_handler(state=GenArt.gen)
@dp.throttled(throttled, rate=300)
async def gen_art_handler(message, state: FSMContext):
    if message.text == 'fin':
        await state.finish()
        await error(message, err_mess='Continue with posts')
        return
    prompt = await data_fetcher.generate_art_prompt(message.chat.id, message.text)
    await message.reply(prompt)
    await message.reply("Send new pub to continue, send `fin` to quit that mode")


@dp.message_handler(state='*')
async def error(message, err_mess=translations.not_understand):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text=translations.generate_plan_cmd))
    await message.reply(err_mess, reply_markup=keyboard)


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
