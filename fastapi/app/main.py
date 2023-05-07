import logging
from functools import lru_cache

import openai
import requests

from fastapi import FastAPI, HTTPException

from .db import linkedin_api, users_db
from .local_settings import (LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET,
                             OPENAI_KEY)

app = FastAPI()

openai.api_key = OPENAI_KEY
scope = ['profile', 'r_liteprofile', 'w_member_social']
redirect_url = 'https://localhost:8432/token?chat_id={}'
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

    print(response)
    access_token = response['access_token']
    # refresh_token = response['refresh_token']

    print("access_token", access_token)
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


def send_publish_post(chat_id, content):
    user_id = get_user_info(chat_id)['id']

    access_token = users_db.get_access_token(chat_id)[0]['access_token']
    headers = get_headers(access_token)
    url = 'https://api.linkedin.com/rest/posts'
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
    data['fullName'] = f"{data['firstName']} {data['lastName']}"
    return data


@app.get("/check_auth")
def check_auth(chat_id):
    tokens = users_db.get_access_token(chat_id)
    return {'is_auth': bool(len(tokens) > 0)}


def prompt_gen_plan(profession, experience, task, n=5):
    return f"""Brief review of my LinkedIn profile: I am {profession}.
My experience: {experience}.
You will create a content plan (headings only) for my LinkedIn blog.
Suggest {n} LinkedIn post topics based on my profession and background, do not use companies I worked for, use different formats.
{task}"""


def format_experience(experience_list):
    out = ''
    for exp in experience_list:
        start_date = f"{exp['timePeriod']['startDate']['year']}-{exp['timePeriod']['startDate']['month']}"
        end_date = 'now'
        if 'endDate' in exp['timePeriod']:
            end_date = f"{exp['timePeriod']['endDate']['year']}-{exp['timePeriod']['endDate']['month']}"
        out += 'Company: {company}; dates: {dates}; position: {position}; description: {descr}. '.format(
            company=f"{exp['companyName']} ({exp['geoLocationName']})",
            dates=f"{start_date} - {end_date}",
            position=exp['title'],
            descr=exp.get("description", "nothing"),
        )
    return out


@app.get("/can_generate_plan")
def check_content_plan(chat_id):
    plan = users_db.get_last_plan(chat_id)
    if plan is None:
        return {'can_generate': True}

    last_id = int(users_db.get_last_post_by_plan(chat_id, plan_date=plan['date']))
    max_plan_id = max(int(k) for k in plan['plan'].keys())
    next_post_id = last_id + 1
    if next_post_id > max_plan_id:
        return {'can_generate': True}

    return {'can_generate': False, 'last_plan': {'data': plan['plan'], 'last_generated_week': last_id}}


@app.get("/generate_content_plan")
def generate_content_plan(chat_id):
    assert check_content_plan(chat_id)['can_generate']

    user_data = users_db.get_info(chat_id)[0]
    occupation = user_data['info']['headline']
    experience = format_experience(user_data['info']['experience'])

    task = 'Week: 1; suggested day to post: Monday; suggested length: 550; format: how-to post; suggested heading:'
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_gen_plan(profession=occupation, experience=experience, task=task, n=5),
        temperature=0.6,
        max_tokens=3100,
    )

    plan = f"{task} {response.choices[0].text}"
    print(plan)
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
    print(kw)
    return {"response": plan}


@app.get('/generate_next_post')
def generate_next_post(chat_id):
    user_data = users_db.get_info(chat_id)[0]
    occupation = user_data['info']['headline']
    experience = format_experience(user_data['info']['experience'])

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
    v = plan[str(next_post_id)]
    topic = v['heading']
    length = v['length']
    post_format = v['format']

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_gen_post(
            profession=occupation,
            experience=experience,
            topic=topic,
            length=length,
            post_format=post_format,
        ),
        max_tokens=3100,
        temperature=0.6,
    )
    generated_post = response.choices[0].text
    next_is_header = False
    header, body = "", ""
    for j, line in enumerate(generated_post.strip().split('\n')):
        if j == 0 and 'Heading' not in line:
            next_is_header = True
        if next_is_header:
            header = line.strip()
            next_is_header = False
            continue
        if not line.strip():
            continue

        if 'Heading:' in line:
            header = line.split('Heading:')[-1].strip()
            if not header:            
                next_is_header = True
        elif 'Body:' in line:
            body = line.split('Body:')[-1].strip() + '\n'
        else:
            body += line + '\n\n'

    header = header.strip(" \n").strip('"')
    content = f'{header}\n\n{body.strip()}'
    users_db.add_post(chat_id, plan_date, next_post_id, content)
    return {"response": content}


def prompt_gen_post(profession, experience, topic, length, post_format):
    return f"""Brief review of my LinkedIn profile: I am {profession}.
My experience: {experience}.
Generate a post for my LinkedIn blog, topic: "{topic}", desired length: {length}, desired format: {post_format}.
Only heading and body. The length must be {length}, pay attention to format.
"""

@app.get('/publish_post')
def publish_post(chat_id):
    last_post_id = users_db.get_last_post_id(chat_id=chat_id)
    post = users_db.get_post(chat_id, last_post_id)[0]
    posted = send_publish_post(chat_id, post['post'])
    return {'is_posted': posted}
