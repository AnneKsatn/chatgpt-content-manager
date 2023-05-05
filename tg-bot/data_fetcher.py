import json
import aiohttp
from local_settings import BACKEND_API
from linkedin_api import Linkedin

async def login(login, password):
    async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + "/login" + "?login=" + login + "&password=" + password
        
        async with session.post(api_url) as response:
            return await response.json()


async def generate_content_plan():
     async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + "/generate_content_plan"
        
        async with session.post(api_url) as response:
            return await response.json()   
