import json
import aiohttp
from local_settings import WORDS_API_URL_RANDOM

async def get_shedule():
    async with aiohttp.ClientSession() as session: 
        async with session.get(WORDS_API_URL_RANDOM) as response:
            return await response.json()


async def get_courses():
    async with aiohttp.ClientSession() as session: 
        async with session.get(WORDS_API_URL_RANDOM) as response:
            return await response.json()



# async def get_lesson(course_id):
#     async with aiohttp.ClientSession() as session: 
#         async with session.get("http://127.0.0.1:3000/lessons" + "?course_id=" + course_id) as response:
#             return await response.json()

async def get_user(phone):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://docker-node-mongo:3000/users" + "?phone_number=" + phone) as response:
            return await response.json()

async def get_user_by_chat(chat_id):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://docker-node-mongo:3000/users" + "?chat_id=" + str(chat_id)) as response:
            return await response.json()


async def get_admins():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://docker-node-mongo:3000/users/admins") as response:
            return await response.json()


async def get_students():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://docker-node-mongo:3000/users/students") as response:
            return await response.json()

async def get_lesson(course_id):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://docker-node-mongo:3000/lessons" + "?course_id=" + course_id) as response:
            return await response.json()


async def register_user(user_id, chat_id):
    path = "http://docker-node-mongo:3000/users/" + user_id

    print("Я отправляю chat_id:", chat_id, "по адресу",  path)

    async with aiohttp.ClientSession() as session:
        # path = "http://127.0.0.1:3000/users/" + user_id
        async with session.patch(path, json={"chat_id": chat_id}) as response:
            return await response.json()