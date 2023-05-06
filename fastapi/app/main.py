import openai
import requests

from fastapi import FastAPI

from .db import linkedin_api, users_db
from .local_settings import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET

app = FastAPI()

scope = ['profile']
scope = ['r_basicprofile']
redirect_url = 'https://localhost:8432/token?chat_id={}'
authorization_base_url = 'https://www.linkedin.com/oauth/v2/authorization'
token_url = 'https://www.linkedin.com/oauth/v2/accessToken'


def headers(access_token):
    gen_headers = {
        'Authorization': f'Bearer {access_token}',
        'cache-control': 'no-cache',
        'X-Restli-Protocol-Version': '2.0.0',
        'Connection': 'Keep-Alive'
    }
    return gen_headers


def get_user_info(headers):
    response = requests.get(' https://api.linkedin.com/v2/me', headers=headers)
    user_info = response.json()
    return user_info


def get_tokens(chat_id, auth_code):
    access_token_url = 'https://www.linkedin.com/oauth/v2/accessToken'

    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_url.format(chat_id),
        'client_id': LINKEDIN_CLIENT_ID,
        'client_secret': LINKEDIN_CLIENT_SECRET,
    }

    response = requests.post(access_token_url, data=data, timeout=30)
    response = response.json()

    print(response)
    access_token = response['access_token']
    refresh_token = response['refresh_token']

    print("access_token", access_token)
    print("refresh_token", refresh_token)
    return {'access_token': access_token, 'refresh_token': refresh_token}
users = {}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/token")
def read_item(chat_id: str, code: str):
    tokens = get_tokens(chat_id, code)
    users_db.add_access_token(chat_id, **tokens)
    return {'success': True}


@app.get("/get_info")
def get_info(chat_id):
    tokens = users_db.get_access_token(chat_id)
    request_headers = headers(tokens['access_token'])
    user_info = get_user_info(request_headers)
    print(user_info)
    # linkedin_api.get_profile()


# @app.post("/login")
# def read_item(chat_id: str, login: str, password):
#     try:
#         print(chat_id, login, password)
#         api = Linkedin(login, password)
#         users[chat_id] = api
#         print(users)

#         # occupation = profile_lite["miniProfile"]["occupation"]
#         # experience = profile_basic["experience"]
#         return {"status": "true"}
#     except :
#         return {"status": "false"}

def prompt_gen_plan(profession, experience, task, n=5):
    return f"""Brief review of my LinkedIn profile: I am {profession}.
My experience: {experience}.
You will create a content plan (headings only) for my LinkedIn blog.
Suggest {n} LinkedIn post topics based on my profession and background, do not use companies I worked for, use different formats.
{task}"""


@app.get("/generate_content_plan")
def generate_content_plan(chat_id):
   task = 'Week: 1; suggested day to post: Monday; suggested length: 550; format: how-to post; suggested heading:'
   profile_lite = users[chat_id].get_user_profile(use_cache=False)
   profile_basic = users[chat_id].get_profile(profile_lite["miniProfile"]["publicIdentifier"])
   
   occupation = profile_lite["miniProfile"]["occupation"]
   experience = profile_basic["experience"]

   response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_gen_plan(profession=occupation, experience=experience, task=task, n=5),
        temperature=0.6,
        max_tokens=3100,
    )
   
   print(f'OpenAI response: {response.choices}')
   return {"response": f'{task} {response.choices[0].text}'}
