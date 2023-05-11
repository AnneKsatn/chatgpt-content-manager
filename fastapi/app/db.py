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
            self.users.updateById(info[0]['id'], {"info": user_info})
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

try:
    linkedin_api = Linkedin(LINKEDIN_LOGIN, LINKEDIN_PASSWORD)
except Exception as e:
    print(e)
    import pickle
    linkedin_api = pickle.loads(b'\x80\x04\x95q\x0e\x00\x00\x00\x00\x00\x00\x8c\x15linkedin_api.linkedin\x94\x8c\x08Linkedin\x94\x93\x94)\x81\x94}\x94(\x8c\x06client\x94\x8c\x13linkedin_api.client\x94\x8c\x06Client\x94\x93\x94)\x81\x94}\x94(\x8c\x07session\x94\x8c\x11requests.sessions\x94\x8c\x07Session\x94\x93\x94)\x81\x94}\x94(\x8c\x07headers\x94\x8c\x13requests.structures\x94\x8c\x13CaseInsensitiveDict\x94\x93\x94)\x81\x94}\x94\x8c\x06_store\x94\x8c\x0bcollections\x94\x8c\x0bOrderedDict\x94\x93\x94)R\x94(\x8c\nuser-agent\x94\x8c\nuser-agent\x94\x8cyMozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36\x94\x86\x94\x8c\x0faccept-encoding\x94\x8c\x0fAccept-Encoding\x94\x8c\rgzip, deflate\x94\x86\x94\x8c\x06accept\x94\x8c\x06Accept\x94\x8c\x03*/*\x94\x86\x94\x8c\nconnection\x94\x8c\nConnection\x94\x8c\nkeep-alive\x94\x86\x94\x8c\x0faccept-language\x94\x8c\x0faccept-language\x94\x8c&en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7\x94\x86\x94\x8c\tx-li-lang\x94\x8c\tx-li-lang\x94\x8c\x05en_US\x94\x86\x94\x8c\x19x-restli-protocol-version\x94\x8c\x19x-restli-protocol-version\x94\x8c\x052.0.0\x94\x86\x94\x8c\ncsrf-token\x94\x8c\ncsrf-token\x94\x8c\x18ajax:3857637688927598933\x94\x86\x94usb\x8c\x07cookies\x94\x8c\x10requests.cookies\x94\x8c\x11RequestsCookieJar\x94\x93\x94)\x81\x94}\x94(\x8c\x07_policy\x94\x8c\x0ehttp.cookiejar\x94\x8c\x13DefaultCookiePolicy\x94\x93\x94)\x81\x94}\x94(\x8c\x08netscape\x94\x88\x8c\x07rfc2965\x94\x89\x8c\x13rfc2109_as_netscape\x94N\x8c\x0chide_cookie2\x94\x89\x8c\rstrict_domain\x94\x89\x8c\x1bstrict_rfc2965_unverifiable\x94\x88\x8c\x16strict_ns_unverifiable\x94\x89\x8c\x10strict_ns_domain\x94K\x00\x8c\x1cstrict_ns_set_initial_dollar\x94\x89\x8c\x12strict_ns_set_path\x94\x89\x8c\x10secure_protocols\x94\x8c\x05https\x94\x8c\x03wss\x94\x86\x94\x8c\x10_blocked_domains\x94)\x8c\x10_allowed_domains\x94N\x8c\x04_now\x94J!\x83Vdub\x8c\x08_cookies\x94}\x94(\x8c\r.linkedin.com\x94}\x94\x8c\x01/\x94}\x94(\x8c\x04lang\x94hC\x8c\x06Cookie\x94\x93\x94)\x81\x94}\x94(\x8c\x07version\x94K\x00\x8c\x04name\x94h_\x8c\x05value\x94\x8c\x0ev=2&lang=en-us\x94\x8c\x04port\x94N\x8c\x0eport_specified\x94\x89\x8c\x06domain\x94h[\x8c\x10domain_specified\x94\x88\x8c\x12domain_initial_dot\x94\x89\x8c\x04path\x94h]\x8c\x0epath_specified\x94\x88\x8c\x06secure\x94\x88\x8c\x07expires\x94N\x8c\x07discard\x94\x88\x8c\x07comment\x94N\x8c\x0bcomment_url\x94N\x8c\x07rfc2109\x94\x89\x8c\x05_rest\x94}\x94\x8c\x08SameSite\x94\x8c\x04None\x94sub\x8c\x04liap\x94ha)\x81\x94}\x94(hdK\x00hehyhf\x8c\x04true\x94hhNhi\x89hj\x8c\r.linkedin.com\x94hk\x88hl\x88hmh]hn\x88ho\x88hpJ!*\xcddhq\x89hrNhsNht\x89hu}\x94\x8c\x08SameSite\x94\x8c\x04None\x94sub\x8c\x07bcookie\x94ha)\x81\x94}\x94(hdK\x00heh\x81hf\x8c*"v=2&0edb33f9-d760-4e34-8a15-3283c9868eb9"\x94hhNhi\x89hj\x8c\r.linkedin.com\x94hk\x88hl\x88hmh]hn\x88ho\x88hpJ\xa1\xb67fhq\x89hrNhsNht\x89hu}\x94\x8c\x08SameSite\x94\x8c\x04None\x94subus\x8c\x11.www.linkedin.com\x94}\x94h]}\x94(\x8c\x05li_at\x94ha)\x81\x94}\x94(hdK\x00heh\x8chf\x8c\x98AQEDARcN21ME_fE6AAABh_HwOkMAAAGIFfy-Q1YAYK484Zz0z6acoar_3kNiqaPtj1wAC60zVQYhXPsrX92AmGKOmxwWlMYyq9DI2Q4FFdW9V3N6Wd8T91OOZZEQMG6W_IolvvMKI_qmTwkoNmxbGpzU\x94hhNhi\x89hjh\x89hk\x88hl\x88hmh]hn\x88ho\x88hpJ\xa1\xb67fhq\x89hrNhsNht\x89hu}\x94(\x8c\x08SameSite\x94\x8c\x04None\x94\x8c\x08HTTPOnly\x94N\x8c\x08HttpOnly\x94Nuub\x8c\nJSESSIONID\x94ha)\x81\x94}\x94(hdK\x00heh\x95hf\x8c\x1a"ajax:3857637688927598933"\x94hhNhi\x89hj\x8c\x11.www.linkedin.com\x94hk\x88hl\x88hmh]hn\x88ho\x88hpJ!*\xcddhq\x89hrNhsNht\x89hu}\x94\x8c\x08SameSite\x94\x8c\x04None\x94sub\x8c\x08bscookie\x94ha)\x81\x94}\x94(hdK\x00heh\x9dhf\x8cX"v=1&2023050616410424240848-daec-4a8f-8f2f-7be664c839aeAQFGZ65rR9jgXiDDTOruJ1JF76IC3yN2"\x94hhNhi\x89hj\x8c\x11.www.linkedin.com\x94hk\x88hl\x88hmh]hn\x88ho\x88hpJ\xa1\xb67fhq\x89hrNhsNht\x89hu}\x94(\x8c\x08HttpOnly\x94N\x8c\x08SameSite\x94\x8c\x04None\x94uubusu\x8c\x04_now\x94J!\x83Vdub\x8c\x04auth\x94N\x8c\x07proxies\x94}\x94\x8c\x05hooks\x94}\x94\x8c\x08response\x94]\x94s\x8c\x06params\x94}\x94\x8c\x06verify\x94\x88\x8c\x04cert\x94N\x8c\x08adapters\x94h\x1a)R\x94(\x8c\x08https://\x94\x8c\x11requests.adapters\x94\x8c\x0bHTTPAdapter\x94\x93\x94)\x81\x94}\x94(\x8c\x0bmax_retries\x94\x8c\x12urllib3.util.retry\x94\x8c\x05Retry\x94\x93\x94)\x81\x94}\x94(\x8c\x05total\x94K\x00\x8c\x07connect\x94N\x8c\x04read\x94\x89\x8c\x06status\x94N\x8c\x05other\x94N\x8c\x08redirect\x94N\x8c\x10status_forcelist\x94\x8f\x94\x8c\x0fallowed_methods\x94(\x8c\x05TRACE\x94\x8c\x03GET\x94\x8c\x07OPTIONS\x94\x8c\x03PUT\x94\x8c\x06DELETE\x94\x8c\x04HEAD\x94\x91\x94\x8c\x0ebackoff_factor\x94K\x00\x8c\x0bbackoff_max\x94Kx\x8c\x11raise_on_redirect\x94\x88\x8c\x0fraise_on_status\x94\x88\x8c\x07history\x94)\x8c\x1arespect_retry_after_header\x94\x88\x8c\x1aremove_headers_on_redirect\x94(\x8c\rauthorization\x94\x91\x94\x8c\x0ebackoff_jitter\x94G\x00\x00\x00\x00\x00\x00\x00\x00ub\x8c\x06config\x94}\x94\x8c\x11_pool_connections\x94K\n\x8c\r_pool_maxsize\x94K\n\x8c\x0b_pool_block\x94\x89ub\x8c\x07http://\x94h\xb7)\x81\x94}\x94(h\xbah\xbd)\x81\x94}\x94(h\xc0K\x00h\xc1Nh\xc2\x89h\xc3Nh\xc4Nh\xc5Nh\xc6\x8f\x94h\xc8h\xcfh\xd0K\x00h\xd1Kxh\xd2\x88h\xd3\x88h\xd4)h\xd5\x88h\xd6(\x8c\rauthorization\x94\x91\x94h\xd9G\x00\x00\x00\x00\x00\x00\x00\x00ubh\xda}\x94h\xdcK\nh\xddK\nh\xde\x89ubu\x8c\x06stream\x94\x89\x8c\ttrust_env\x94\x88\x8c\rmax_redirects\x94K\x1eubh\xa8}\x94\x8c\x06logger\x94\x8c\x07logging\x94\x8c\tgetLogger\x94\x93\x94h\x06\x85\x94R\x94\x8c\x08metadata\x94}\x94(\x8c\x19clientApplicationInstance\x94}\x94(\x8c\x0eapplicationUrn\x94\x8c,urn:li:application:(voyager-web,voyager-web)\x94\x8c\x07version\x94\x8c\t1.12.4856\x94\x8c\ntrackingId\x94]\x94(J\xb1\xff\xff\xffK%K&K#J\xb3\xff\xff\xffJ\x8b\xff\xff\xffKBKcJ\xa2\xff\xff\xffJ\xcc\xff\xff\xffKMKlKSK5J\xcb\xff\xff\xffJ\x81\xff\xff\xffeu\x8c\x14clientPageInstanceId\x94\x8c$c3ad9c0c-114a-4848-b58a-dd929723a1eb\x94u\x8c\x11_use_cookie_cache\x94\x88\x8c\x12_cookie_repository\x94\x8c\x1elinkedin_api.cookie_repository\x94\x8c\x10CookieRepository\x94\x93\x94)\x81\x94}\x94\x8c\x0bcookies_dir\x94\x8c"/Users/sind/.linkedin_api/cookies/\x94sbubh\xech\xefh\x00\x85\x94R\x94ub.')
