

import logging
import random
from dataclasses import asdict, dataclass

import openai

POST_FORMATS = ['how-to guide', 'story', 'interview', 'listicle', 'case study', 'opinion piece']


@dataclass
class OpenAICompletion:
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.6
    max_tokens: int = 3100

    def call_chat_completion(self, messages):
        response = openai.ChatCompletion.create(
            messages=messages,
            **(asdict(self))
        )
        return response.choices[0]['message']['content']


default_openai = OpenAICompletion()


def openai_generate_content_plan(profession, experience, n=5,
                                 openai_wrapper: OpenAICompletion = default_openai):
    role = 'You are content manager of LinkedIn personal text blog. '\
           'You create content plan (day to post, size, format, heading).'

    task = f'Week: 1; suggested day to post: Monday; suggested length: 550; '\
           f'format: {random.choice(POST_FORMATS)}; suggested heading:'

    task_prompt = f'I am {profession}. My experience: {experience}.'\
           f'Suggest {n} text post topics, do not use companies I worked for, use different formats.' \
           f'{task}'

    response = openai_wrapper.call_chat_completion(
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": task_prompt},
        ]
    )
    plan = f"{task} {response}"
    return plan


def openai_generate_post(profession, experience, topic, length, post_format,
                         openai_wrapper: OpenAICompletion = default_openai):
    role = 'You are ghost-writer of LinkedIn personal text blog. ' \
           'You write text posts by specification of topic, length and format.'
    task = f'I am {profession}, my experience: {experience}. ' \
           f'Generate a text post {topic} of length: {length} symbols in format of {post_format}, only body.'

    generated_post = openai_wrapper.call_chat_completion(
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": task},
        ]
    )
    return generated_post
