from linkedin_api import Linkedin
from pysondb import db

from .local_settings import LINKEDIN_LOGIN, LINKEDIN_PASSWORD


class UsersDB:
    def __init__(self, name) -> None:
        self.db = self.get_db(name)
    
    @classmethod
    def get_db(cls, name):
        return db.getDb(f'dbs/{name}.json')

    def add_access_token(self, chat_id, access_token, refresh_token=''):
        self.db.add({'name': chat_id, 'type': "tokens", 'access_token': access_token, 'refresh_token': refresh_token})

    def get_access_token(self, chat_id):
        return self.db.getByQuery({'name': chat_id, 'type': 'tokens'})
    
    def add_info(self, chat_id, user_info):
        self.db.add({'name': chat_id, 'type': "info", 'info': user_info})
    
    def get_info(self, chat_id):
        return self.db.getByQuery({'name': chat_id, 'type': 'info'})
    
    def add_plan(self, chat_id, plan):
        self.db.add({'name': chat_id, 'plan': plan, 'type': 'plan'})
    
    def get_plan(self, chat_id):
        return self.db.getByQuery({'name': chat_id, 'type': 'plan'})

    def add_post(self, chat_id, post_id, post):
        self.db.add({'name': chat_id, 'post_id': post_id, 'post': post, 'type': 'post'})

    def get_last_post_id(self, chat_id):
        posts = self.db.getByQuery({'name': chat_id, 'type': 'post'})
        if posts:
            last_post_id = max(p['post_id'] for p in posts)
        else:
            last_post_id = 0
        return last_post_id

    def get_post(self, chat_id, post_id):
        return self.db.getByQuery({'name': chat_id, 'post_id': post_id})


users_db = UsersDB('users')

linkedin_api = Linkedin(LINKEDIN_LOGIN, LINKEDIN_PASSWORD)
