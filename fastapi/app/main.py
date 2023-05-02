from typing import Union
from requests_oauthlib import OAuth2Session
from .local_settings import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
from fastapi import FastAPI
import uvicorn

app = FastAPI()

scope = ['r_liteprofile']
redirect_url = 'https://localhost:8432/token'
authorization_base_url = 'https://www.linkedin.com/oauth/v2/authorization'
token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
linkedin = OAuth2Session(LINKEDIN_CLIENT_ID, redirect_uri=redirect_url, scope=scope)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/token")
def read_item(code: str):
    redirect_response = "https://localhost:8432/token?code=" + code
    linkedin.fetch_token(
        token_url, 
        client_secret=LINKEDIN_CLIENT_SECRET,
        include_client_id=True,
        authorization_response=redirect_response)
    
    r = linkedin.get('https://api.linkedin.com/v2/me')
    return {"code": r.content}

