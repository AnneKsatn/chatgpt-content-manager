from linkedin_api import Linkedin
from pysondb import db

from .local_settings import LINKEDIN_LOGIN, LINKEDIN_PASSWORD


class UsersDB:
    def __init__(self, name) -> None:
        self.db = self.get_db(name)
    
    @classmethod
    def get_db(cls, name):
        return db.getDb(f'dbs/{name}.json')

    def add_access_token(self, chat_id, access_token, refresh_token):
        self.db.add({'name': chat_id, 'type': "tokens", 'access_token': access_token, 'refresh_token': refresh_token})

    def get_access_token(self, chat_id):
        return self.db.getBy({'name': chat_id})


users_db = UsersDB('users')

linkedin_api = Linkedin(LINKEDIN_LOGIN, LINKEDIN_PASSWORD)
