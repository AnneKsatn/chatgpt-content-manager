import enum
import logging
import random
from functools import lru_cache
from typing import Annotated

import openai
import requests
from pydantic import BaseModel

from fastapi import Body, FastAPI, HTTPException

from .db import linkedin_api, users_db
from .local_settings import (BACKEND_API, LINKEDIN_CLIENT_ID,
                             LINKEDIN_CLIENT_SECRET, OPENAI_KEY)
from .prompts import (openai_generate_art_prompt, openai_generate_content_plan,
                      openai_generate_image_by_prompt, openai_generate_post)

app = FastAPI()

class Mode(enum.Enum):
    ALWAYS_GENERATE = 'always_gen'
    PROD = 'prod'
MODE = Mode.ALWAYS_GENERATE

openai.api_key = OPENAI_KEY
scope = ['profile', 'r_liteprofile', 'w_member_social']
redirect_url = BACKEND_API + '/token?chat_id={}'
authorization_base_url = 'https://www.linkedin.com/oauth/v2/authorization'
token_url = 'https://www.linkedin.com/oauth/v2/accessToken'


def get_headers(access_token):
    gen_headers = {
        'Authorization': f'Bearer {access_token}',
        'cache-control': 'no-cache',
        'X-Restli-Protocol-Version': '2.0.0',
        'Connection': 'Keep-Alive',
        'LinkedIn-Version': '202303'
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

    logging.debug(response.keys())
    access_token = response.get('access_token', None)
    if not access_token:
        raise RuntimeError('Failed to retrieve token')
    # refresh_token = response['refresh_token']
    # print("refresh_token", refresh_token)
    return {'access_token': access_token}


def api_get(token, url):
    gen_headers = {
        'Authorization': f'Bearer {token}',
        'cache-control': 'no-cache',
        'X-Restli-Protocol-Version': '2.0.0',
        'Connection': 'Keep-Alive'
    }

    response = requests.get(url, headers=gen_headers, timeout=30)
    return response


@lru_cache
def get_user_info(chat_id):
    access_token = users_db.get_access_token(chat_id)[0]['access_token']
    headers = get_headers(access_token)
    self_info_url = 'https://api.linkedin.com/v2/me'
    user_info = requests.get(self_info_url, headers=headers, timeout=30)
    return user_info.json()


def send_publish_post(chat_id, content, images):
    user_id = get_user_info(chat_id)['id']

    access_token = users_db.get_access_token(chat_id)[0]['access_token']
    headers = get_headers(access_token)
    url = 'https://api.linkedin.com/rest/posts'

    image_id = None
    if len(images):
        # upload image
        image_upload_init_url = 'https://api.linkedin.com/rest/images?action=initializeUpload'
        payload = {
            "initializeUploadRequest": {
                "owner": f"urn:li:person:{user_id}",
            }
        }
        resp = requests.post(url=image_upload_init_url, headers=headers, json=payload)
        if resp.status_code >= 300 or resp.status_code < 200:
            raise RuntimeError(f'Failed to create image upload url: {resp}, {resp.text}')

        upload_url = resp.json()["value"]["uploadUrl"]
        image_id = resp.json()["value"]["image"]
        req = requests.put(url=upload_url,
                           headers=headers,
                           files={
                               "upload_file": requests.get(images[0], stream=True).raw
                           })
        if req.status_code >= 300 or req.status_code < 200:
            raise RuntimeError(f'Failed to upload image: {resp.text}')

    payload = {
        "author": f"urn:li:person:{user_id}",
        "commentary": content,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    if image_id:
        payload["content"] = {
            "media": {
                "title": content.split('\n')[0],
                "id": image_id
            }
        }
    resp = requests.post(url=url, headers=headers, json=payload)
    if resp.status_code >= 300 or resp.status_code < 200:
        raise RuntimeError(f'Failed to publish post: {resp.text}')
    print(resp.json())
    return resp.json()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/token")
def read_item(chat_id: str, code: str):
    tokens = get_tokens(chat_id, code)
    users_db.add_access_token(chat_id, **tokens)
    return {'success': True}


@app.get("/get_info")
def get_info(chat_id, account_id):
    data = linkedin_api.get_profile(account_id)
    logging.debug(f'Fetched info for `{account_id}`')
    users_db.add_info(chat_id, data)
    data['fullName'] = f"{data.get('firstName', 'unknown')} {data.get('lastName', 'unknown')}"
    return data


@app.get("/check_auth")
def check_auth(chat_id):
    tokens = users_db.get_access_token(chat_id)
    return {'is_auth': bool(len(tokens) > 0)}


def format_plan(plan, last_generated_id):
    res = ''
    for d in plan.values():
        res += f'Week: {d["week"]}\nDay of post: {d["day to post"]}\nFormat: {d["format"]}\nLength: {d["length"]}\nTopic: {d["heading"]}\n\n'
    res += f'Last generated post for week: {last_generated_id}\n\n'
    return res


@app.get("/can_generate_plan")
def check_content_plan(chat_id):
    if MODE == Mode.ALWAYS_GENERATE:
        return {'can_generate': True}

    plan = users_db.get_last_plan(chat_id)
    if plan is None:
        return {'can_generate': True}

    last_id = int(users_db.get_last_post_by_plan(chat_id, plan_date=plan['date']))
    max_plan_id = max(int(k) for k in plan['plan'].keys())
    next_post_id = last_id + 1
    if next_post_id > max_plan_id:
        return {'can_generate': True}

    return {'can_generate': False, 'last_plan': format_plan(plan['plan'], last_id)}


def parse_period(period):
    per = str(period.get('year', ''))
    month = period.get('month', '')
    if month:
        per += f'-{month}'
    return per


def parse_time_period(time_period):
    start_date = parse_period(time_period.get('startDate', {})) or 'before'
    end_date = parse_period(time_period.get('endDate', {})) or 'now'
    return start_date, end_date
    

def format_experience(experience_list):
    out = ''
    if not len(experience_list):
        logging.warning('Experience list is empty!')
        return ''
    for exp in experience_list:
        start_date, end_date = parse_time_period(exp.get('timePeriod', {}))
        out += 'Company: {company}; dates: {dates}; position: {position}; description: {descr}; '.format(
            company=f"{exp['companyName']} ({exp.get('geoLocationName', exp.get('locationName', '`location not stated`'))})",
            dates=f"{start_date} - {end_date}",
            position=exp.get('title', 'title not stated'),
            descr=exp.get("description", "nothing"),
        )
    return out


@app.get("/generate_content_plan")
def generate_content_plan(chat_id):
    assert MODE == Mode.ALWAYS_GENERATE or check_content_plan(chat_id)['can_generate']

    user_data = users_db.get_info(chat_id)[0]
    user_info = user_data.get('info', user_data)
    occupation = user_info.get('headline', '`hidden profession`')
    experience = format_experience(user_info.get('experience', []))

    plan = openai_generate_content_plan(
        profession=occupation,
        experience=experience,
    )
    logging.debug(f"For {chat_id} generated plan: {plan}")
    kw = {}
    for line in plan.split('\n'):
        if not line:
            continue
        data = {}
        items = line.split(';')
        for item in items:
            k, *v = item.split(':')
            k = k.strip().lower()
            if 'suggested' in k:
                k = ' '.join(k.split(' ')[1:])
            data[k] = ': '.join(_v.strip() for _v in v)
        kw[data['week']] = data

    users_db.add_plan(chat_id, kw)
    return {"response": plan.replace(';', '\n')}


@app.get('/generate_next_post')
def generate_next_post(chat_id):
    user_data = users_db.get_info(chat_id)[0]
    user_info = user_data.get('info', {})
    occupation = user_info.get('headline', '`hidden profession`')
    experience = format_experience(user_info.get('experience', []))

    plan = users_db.get_last_plan(chat_id)
    if not plan:
        raise HTTPException(status_code=400, detail='Plan not found')

    plan_date = plan.get('date', '0')
    plan = plan['plan']
    last_id = int(users_db.get_last_post_by_plan(chat_id, plan_date=plan_date))
    max_plan_id = max(int(k) for k in plan.keys())
    next_post_id = last_id + 1
    if next_post_id > max_plan_id:
        raise HTTPException(status_code=409, detail='Failed to create post, plan has ended')

    logging.info(f'{chat_id}: {plan}')
    post_meta = plan[str(next_post_id)]
    topic = post_meta['heading']
    length = post_meta['length']
    post_format = post_meta['format']

    content = openai_generate_post(profession=occupation, experience=experience, topic=topic,
                                   length=length, post_format=post_format)
    final_content = f'{topic}\n\n{content}'
    users_db.add_post(chat_id, plan_date, next_post_id, final_content)

    prompt = openai_generate_art_prompt(topic=topic, post_format=post_format, publication=content)
    images = openai_generate_image_by_prompt(prompt=prompt)
    users_db.add_art(chat_id, plan_date, next_post_id, prompt, images)

    return {"meta": post_meta, "art_prompt": prompt, "images": images, "response": content}


@app.get('/publish_post')
def publish_post(chat_id):
    last_plan = users_db.get_last_plan(chat_id=chat_id)
    if not last_plan:
        raise HTTPException(status_code=404, detail='Plan or post not found')

    last_post_id = users_db.get_last_post_by_plan(chat_id=chat_id, plan_date=last_plan['date'])
    last_art = users_db.get_last_art_by_plan(chat_id, plan_date=last_plan['date'])
    if not last_art:
        last_art = [{'images': []}]
    post = users_db.get_post(chat_id, last_post_id)[0]
    posted = send_publish_post(chat_id, post['post'], last_art[0]['images'])
    return {'is_posted': posted}


class ArtPromptParams(BaseModel):
    chat_id: str
    text: str


@app.post('/generate_art_prompt')
def gen_art_prompt(params: Annotated[ArtPromptParams, Body(embed=True)]):
    prompt = openai_generate_art_prompt(
        topic=params.text.split('\n')[0],
        post_format=params.text.split('\n')[1],
        publication='\n'.join(params.text.split('\n')[2:])
    )

    return {"response": prompt}
