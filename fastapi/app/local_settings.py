import json

LINKEDIN_CLIENT_ID = "78ydgx7xxjf0dz"
LINKEDIN_CLIENT_SECRET = "DArwc9bJkfMfKvTY"
LINKEDIN_LOGIN = ''
LINKEDIN_PASSWORD = ''

_creds = json.load(open('credentials.json'))
LINKEDIN_LOGIN = _creds['login']
LINKEDIN_PASSWORD = _creds['password']
