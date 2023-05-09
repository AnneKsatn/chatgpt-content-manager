import random
from dataclasses import asdict, dataclass
from typing import List

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

    def call_image_generation(self, prompt, n=1, size='1024x1024') -> List[str]:
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size
        )
        image_urls = [u['url'] for u in response['data']]
        return image_urls


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


def openai_generate_art_prompt(topic, publication, post_format,
                               openai_wrapper: OpenAICompletion = default_openai):
    role = 'You are art prompts generator. ' \
           'You generate short art prompts for illustrations to text posts in LinkedIn blog by publication title and text.'
    task = f'Title: {topic}; format: {post_format}; text: {publication};\ngenerate short art prompt (up to 30 words)'

    generated_prompt = openai_wrapper.call_chat_completion(
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": task},
        ]
    )
    return generated_prompt


def openai_generate_image_by_prompt(prompt, openai_wrapper: OpenAICompletion = default_openai):
    return openai_wrapper.call_image_generation(prompt=prompt + ". no text.")
