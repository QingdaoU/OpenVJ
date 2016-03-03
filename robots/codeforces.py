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

    def get_problem(self, url):
        r = self.get(url, headers={"Referer": "https://codeforces.com"})
        regex = {"title": r"<div class=\"header\"><div class=\"title\">([\s\S]*?)</div>",
                 "time_limit": r"<div class=\"time-limit\"><div class=\"property-title\">time limit per test</div>(\d+)\s*seconds</div>",
                 "memory_limit": r"<div class=\"memory-limit\"><div class=\"property-title\">memory limit per test</div>(\d+)\s*megabytes</div>",
                 "description": r"<div class=\"output-file\"><div class=\"property-title\">output</div>[\s\S]*?</div></div><div>([\s\S]*?)</div>",
                 "input_description": r"<div class=\"section-title\">Input</div>([\s\S]*?)</div>",
                 "output_description": r"<div class=\"section-title\">Output</div>([\s\s]*?)</div>"}
        input_samples_regex = r"<div class=\"title\">Input</div><pre>([\s\S]*?)</pre></div>"
        output_samples_regex = r"<div class=\"title\">Output</div><pre>([\s\S]*?)</pre></div>"
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            print(k, items)
            if not items:
                raise RegexError("No such data")
            data[k] = self._clean_html(items[0])

        data["samples"] = []
        input_samples = re.compile(input_samples_regex).findall(r.text)
        output_samples = re.compile(output_samples_regex).findall(r.text)
        for i in range(len(input_samples)):
            data["samples"].append({"input": self._clean_html(input_samples[i]), "output": self._clean_html(output_samples[i])})
        return data