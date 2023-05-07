import typing

import aiohttp
from local_settings import BACKEND_API


async def publish_post(chat_id):
    async with aiohttp.ClientSession() as session: 
        publish = BACKEND_API + f"/publish_post?chat_id={chat_id}"

        async with session.get(publish, verify_ssl=False) as response:
            return await response.json()


async def check_auth(chat_id):
    async with aiohttp.ClientSession() as session: 
        is_authed = BACKEND_API + f"/check_auth?chat_id={chat_id}"

        async with session.get(is_authed, verify_ssl=False) as response:
            return await response.json()


async def get_info(chat_id, account_id):
    async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + f"/get_info?chat_id={chat_id}&account_id={account_id}"

        async with session.get(api_url, verify_ssl=False) as response:
            return await response.json()


async def generate_content_plan(chat_id):
     async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + f'/generate_content_plan?chat_id={chat_id}'
        
        async with session.get(api_url, verify_ssl=False) as response:
            return await response.json()


async def generate_next_post(chat_id):
     async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + f'/generate_next_post?chat_id={chat_id}'
        
        async with session.get(api_url, verify_ssl=False) as response:
            if response.status == 200:
                return await response.json()
            text = await response.text()
            return {'success': False, 'error': text}


async def can_generate_plan(chat_id) -> typing.Tuple[bool, str]:
     async with aiohttp.ClientSession() as session: 
        api_url = BACKEND_API + f'/can_generate_plan?chat_id={chat_id}'
        
        async with session.get(api_url, verify_ssl=False) as response:
            resp = await response.json()
            return resp['can_generate'], resp.get('last_plan', None)
