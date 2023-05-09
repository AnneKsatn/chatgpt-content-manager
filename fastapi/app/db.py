from datetime import datetime

from linkedin_api import Linkedin
from pysondb import db

from .local_settings import LINKEDIN_LOGIN, LINKEDIN_PASSWORD


class AppDB:
    def __init__(self) -> None:
        self.users = self.get_db('users')
        self.posts = self.get_db('posts')
        self.plans = self.get_db('plans')
        self.tokens = self.get_db('tokens')
        self.arts = self.get_db('arts')
    
    @classmethod
    def get_db(cls, name):
        return db.getDb(f'dbs/{name}.json')

    def add_access_token(self, chat_id, access_token, refresh_token=''):
        self.tokens.add({'name': chat_id, 'type': "tokens", 'access_token': access_token, 'refresh_token': refresh_token})

    def get_access_token(self, chat_id):
        return self.tokens.getByQuery({'name': chat_id, 'type': 'tokens'})
    
    def add_info(self, chat_id, user_info):
        if info := self.get_info(chat_id=chat_id):
            self.users.updateById(info['id'], {"info": user_info})
            return
        self.users.add({'name': chat_id, 'type': "info", 'info': user_info})
    
    def get_info(self, chat_id):
        return self.users.getByQuery({'name': chat_id, 'type': 'info'})
    
    def add_plan(self, chat_id, plan):
        self.plans.add({'name': chat_id, 'plan': plan, 'type': 'plan', 'date': datetime.now().strftime('%Y%m%d%H%M%S')})
    
    def get_plan(self, chat_id):
        return self.plans.getByQuery({'name': chat_id, 'type': 'plan'})
    
    def get_last_plan(self, chat_id):
        plans = self.plans.getByQuery({'name': chat_id, 'type': 'plan'})
        plans.sort(key=lambda k: k.get('date', '0'))
        if plans:
            return plans[-1]
        return None

    def add_post(self, chat_id, plan_date, post_id, post):
        self.posts.add({'name': chat_id, 'plan_date': plan_date, 'post_id': post_id, 'post': post, 'type': 'post'})

    def get_last_post_by_plan(self, chat_id, plan_date):
        posts = self.posts.getByQuery({'name': chat_id, 'plan_date': plan_date, 'type': 'post'})
        if posts:
            last_post_id = max(p['post_id'] for p in posts)
        else:
            last_post_id = 0
        return last_post_id

    def get_post(self, chat_id, post_id):
        return self.posts.getByQuery({'name': chat_id, 'post_id': post_id})

    def add_art(self, chat_id, plan_date, post_id, prompt, images):
        self.arts.add({'name': chat_id, 'plan_date': plan_date, 'post_id': post_id, 'prompt': prompt, 'type': 'prompt', 'images': images})

    def get_last_art_by_plan(self, chat_id, plan_date):
        last_post_id = self.get_last_post_by_plan(chat_id, plan_date)
        return self.arts.getByQuery({'name': chat_id, 'plan_date': plan_date, 'post_id': last_post_id, 'type': 'prompt'})


users_db = AppDB()

linkedin_api = Linkedin(LINKEDIN_LOGIN, LINKEDIN_PASSWORD)
