import logging

import openai
import requests

from fastapi import FastAPI

from .db import linkedin_api, users_db
from .local_settings import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET

app = FastAPI()

scope = ['profile', 'r_liteprofile', 'w_member_social']
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
    # refresh_token = response['refresh_token']

    print("access_token", access_token)
    # print("refresh_token", refresh_token)
    return {'access_token': access_token}


def publish_post(chat_id, content):
    access_token = users_db.get_access_token(chat_id)[0]['access_token']
    url = 'https://api.linkedin.com/rest/posts'
    headers = headers(access_token)
    payload = {
        "author": "urn:li:organization:5515715",
        "commentary": {content},
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    resp = requests.post(url=url, headers=headers, data=payload)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to publish post: {resp.text}')
    return True


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
    # tokens = users_db.get_access_token(chat_id)
    # request_headers = headers(tokens['access_token'])
    # user_info = get_user_info(request_headers)
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
        end_date = "now" if not exp['timePeriod'].get('endDate', None) \
            else f"{exp['timePeriod']['endDate']['year']}-{exp['endDate']['startDate']['month']}"
        out += 'Company: {company}; dates: {dates}; position: {position}; description: {descr}. '.format(
            company=f"{exp['companyName']} ({exp['geoLocationName']})",
            dates=f"{start_date} - {end_date}",
            position=exp['title'],
            descr=exp["description"],
        )
    return out


@app.get("/generate_content_plan")
def generate_content_plan(chat_id):
    data = users_db.get_info(chat_id)
    occupation = data['headline']
    experience = format_experience(data['experience'])

    task = 'Week: 1; suggested day to post: Monday; suggested length: 550; format: how-to post; suggested heading:'
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_gen_plan(profession=occupation, experience=experience, task=task, n=5),
        temperature=0.6,
        max_tokens=3100,
    )

    plan = f"{task} {response.choices[0].text}"
    kw = {}
    for line in plan.split('\n\n'):
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
    return {"response": plan}


@app.get('/generate_next_post')
def generate_next_post(chat_id):
    data = users_db.get_info(chat_id)
    occupation = data['headline']
    experience = format_experience(data['experience'])

    plan = users_db.get_plan(chat_id)
    last_id = users_db.get_last_post_id(chat_id)
    max_plan_id = max(plan['plan'].keys())
    next_post_id = last_id + 1
    if next_post_id > max_plan_id:
        raise RuntimeError('Failed to create post, plan has ended')

    v = plan[next_post_id]
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
    content = f'{header}\n{body.strip()}'
    users_db.add_post(next_post_id, content)
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
    post = users_db.get_post(chat_id, last_post_id)
    posted = publish_post(chat_id, post)
    return {'is_posted': posted}
