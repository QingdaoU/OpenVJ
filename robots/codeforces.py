# coding=utf-8
import re
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


class CodeForcesRobot(Robot):
    def __init__(self, cookies=None):
        super().__init__(cookies=cookies)
        self.token = ""

    def check_url(self, url):
        return re.compile(r"^http://codeforces.com/problemset/problem/\d+/[A-Z]$").match(url) is not None

    def _get_token(self):
        r = self.get("http://codeforces.com/enter", headers={"Referer": "http://codeforces.com/enter"})
        self.check_status_code(r)
        self.token = re.compile(r"<meta name=\"X-Csrf-Token\" content=\"([\s\S]*?)\"/>").findall(r.text)[0]
        self.cookies = dict(r.cookies)

    def login(self, username, password):
        self._get_token()
        r = self.post("http://codeforces.com/enter",
                      data={"csrf_token": self.token, "action": "enter", "handle": username,
                            "password": password, "remember": "on"},
                      cookies=self.cookies)
        if r.status_code != 302:
            raise AuthFailed("Failed to login PAT")
        self.cookies = dict(r.cookies)

    def is_logged_in(self):
        r = self.get("http://codeforces.com/settings/general", cookies=self.cookies)
        return r.status_code == 200