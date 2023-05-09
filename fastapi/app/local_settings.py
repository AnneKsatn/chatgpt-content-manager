import json
from pathlib import Path

LINKEDIN_CLIENT_ID = "78ydgx7xxjf0dz"
LINKEDIN_CLIENT_SECRET = "DArwc9bJkfMfKvTY"
LINKEDIN_LOGIN = ''
LINKEDIN_PASSWORD = ''

_creds = json.load(open(Path(__file__).parent / 'credentials.json'))
LINKEDIN_LOGIN = _creds['login']
LINKEDIN_PASSWORD = _creds['password']
OPENAI_KEY = _creds['openai_key']
