from typing import Union
from .local_settings import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
from fastapi import FastAPI
import uvicorn
import requests
from linkedin_api import Linkedin
import openai


app = FastAPI()

scope = ['r_basicprofile']
redirect_url = 'https://localhost:8432/token'
authorization_base_url = 'https://www.linkedin.com/oauth/v2/authorization'
token_url = 'https://www.linkedin.com/oauth/v2/accessToken'

users = {}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/login")
def read_item(chat_id: str, login: str, password):
    try:
        print(chat_id, login, password)
        api = Linkedin(login, password)
        users[chat_id]=api
        print(users)

        # occupation = profile_lite["miniProfile"]["occupation"]
        # experience = profile_basic["experience"]
        return {"status": "true"}
    except :
        return {"status": "false"}

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