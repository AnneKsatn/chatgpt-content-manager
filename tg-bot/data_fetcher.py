import aiohttp
from local_settings import BACKEND_API


async def get_info(chat_id):
    async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + f"/get_info?chat_id={chat_id}"

        async with session.post(api_url) as response:
            return await response.json()


async def login(chat_id, login, password):
    async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + "/login" + "?chat_id="+ str(chat_id) + "&login=" + login + "&password=" + password
        
        async with session.post(api_url) as response:
            return await response.json()


async def generate_content_plan(chat_id):
     async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + "/generate_content_plan" + "?chat_id=" + chat_id
        
        async with session.get(api_url) as response:
            return await response.json()   
