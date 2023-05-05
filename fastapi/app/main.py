from typing import Union
from .local_settings import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
from fastapi import FastAPI
import uvicorn
import requests
from linkedin_api import Linkedin


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
def read_item(login: str, password):
    try:
        api = Linkedin(login, password)
        profile_lite = api.get_user_profile(use_cache=False)
        profile_basic = api.get_profile(profile_lite["miniProfile"]["publicIdentifier"])

        users[login]=api
        print(users)

        # occupation = profile_lite["miniProfile"]["occupation"]
        # experience = profile_basic["experience"]
        return {"status": "true"}
    except :
        return {"status": "false"}

@app.post("/generate_content_plan")
def generate_content_plan(profession, experience):
    task = 'Week: 1; suggested day to post: Monday; suggested length: 550; format: how-to post; suggested heading:'
    # form = request.get_json()
    # profession = form["profession"]
    # experience = form["experience"]
    # length = form.get("n", 5)
    # response = openai.Completion.create(
    # model="text-davinci-003",
    # prompt=prompt_gen_plan(profession=profession, experience=experience, task=task, n=length),
    # temperature=0.6,
    # max_tokens=3100,
    # )
    # print(f'OpenAI response: {response.choices}')
    # return jsonify({"response": f'{task} {response.choices[0].text}'})
