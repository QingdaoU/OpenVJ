# coding=utf-8
import re
import json
from .robot import Robot
from .exceptions import AuthFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


class CodeForcesRobot(Robot):
    def __init__(self, cookies=None, token=""):
        super().__init__(cookies=cookies)
        self.token = token

    def save(self):
        return {"cookies": self.cookies, "token": self.token}

    def check_url(self, url):
        return re.compile(r"^https://codeforces.com/problemset/problem/\d+/[A-Z]$").match(url) is not None

    def _get_token(self):
        r = self.get("https://codeforces.com/problemset", headers={"Referer": "http://codeforces.com/problemset"}, cookies=self.cookies)
        self.check_status_code(r)
        self.token = re.compile(r'<meta name="X-Csrf-Token" content="([\s\S]*?)"/>').findall(r.text)[0]
        self.cookies.update(dict(r.cookies))

    def login(self, username, password):
        self._get_token()
        r = self.post("https://codeforces.com/enter",
                      data={"csrf_token": self.token, "action": "enter", "handleOrEmail": username,
                            "password": password, "remember": "on"},
                      cookies=self.cookies)
        if r.status_code != 302:
            raise AuthFailed("Failed to login CodeForces")
        self.cookies.update(dict(r.cookies))
        self._get_token()

    @property
    def is_logged_in(self):
        r = self.get("https://codeforces.com/settings/general", cookies=self.cookies)
        return r.status_code == 200

    def get_problem(self, url):
        r = self.get(url, headers={"Referer": "https://codeforces.com"})
        regex = {"title": r'<div class="header"><div class="title">([\s\S]*?)</div>',
                 "time_limit": r'<div class="time-limit"><div class="property-title">time limit per test</div>(\d+)\s*second',
                 "memory_limit": r'<div class="memory-limit"><div class="property-title">memory limit per test</div>(\d+)\s*megabytes</div>',
                 "description": r'<div class="output-file"><div class="property-title">output</div>[\s\S]*?</div></div><div>([\s\S]*?)</div>',
                 "input_description": r'<div class="section-title">Input</div>([\s\S]*?)</div>',
                 "hint": r'<div class="note"><div class="section-title">Note</div>([\s\S]*?)</div>',
                 "output_description": r'<div class="section-title">Output</div>([\s\S]*?)</div>'}
        input_samples_regex = r'<div class="title">Input</div><pre>([\s\S]*?)</pre></div>'
        output_samples_regex = r'<div class="title">Output</div><pre>([\s\S]*?)</pre></div>'
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                if k == "hint":
                    data[k] = None
                    continue
                raise RegexError("No such data")
            data[k] = self._clean_html(items[0])

        data["samples"] = []
        data["memory_limit"] = int(data["memory_limit"])
        data["time_limit"] = int(data["time_limit"]) * 1000
        input_samples = re.compile(input_samples_regex).findall(r.text)
        output_samples = re.compile(output_samples_regex).findall(r.text)
        for i in range(len(input_samples)):
            data["samples"].append({"input": self._clean_html(input_samples[i]), "output": self._clean_html(output_samples[i])})
        data["id"] = re.compile("problem/([\s\S]*)").findall(url)
        data["submit_url"] = "https://codeforces.com/problemset/submit"
        return data

    def submit(self, submit_url, language, code, origin_id):
        if language == Language.C:
            language = "43"
        elif language == Language.CPP:
            language = "42"
        else:
            language = "36"

        r = self._request("post", url=submit_url + "?csrf_token=" + self.token,
                          files={"sourcefile": (" ", ""),
                                 "csrf_token": ('', self.token),
                                 "action": ('', "submitsolutionformsubmitted"),
                                 "submittedProblemCode": ('', origin_id),
                                 "programTypeId": ('', language),
                                 "source": ('', code),
                                 "tabSize  ": ('', "4")},
                          cookies=self.cookies,
                          headers={"Referer": submit_url})

        if re.compile(r"You have submitted exactly the same code before").search(r.text) is not None:
            raise SubmitProblemFailed("You have submitted exactly the same code before")

        if re.compile(r"Source should satisfy regex").search(r.text) is not None:
            raise SubmitProblemFailed("Source should satisfy regex [^{}]*public\s+(final)?\s*class\s+(\w+).*")

        if re.compile(r"\<title\>Codeforces\</title\>").search(r.text) is not None:
            raise SubmitProblemFailed("Failed to submit problem, url: %s code %d" % (submit_url, r.status_code))

    def get_result(self, submission_id, username):
        status_url = "https://codeforces.com/api/user.status?handle=" + username + "&from=1&count=1"
        s = json.loads(self.get(status_url).text)
        data = {}
        data["cpu_time"] = s["result"][0]["timeConsumedMillis"]
        data["memory"] = s["result"][0]["memoryConsumedBytes"] // 1024
        # 没有开始判题之前,没有这个字段
        if "verdict" not in s["result"][0]:
            data["result"] = "TESTING"
        else:
            data["result"] = s["result"][0]["verdict"]

        if data["result"] == "OK":
            data["result"] = Result.accepted
        elif data["result"] == "WRONG_ANSWER":
            data["result"] = Result.wrong_answer
        elif data["result"] == "TIME_LIMIT_EXCEEDED":
            data["result"] = Result.time_limit_exceeded
        elif data["result"] == "COMPILATION_ERROR":
            data["result"] = Result.compile_error
        elif data["result"] == "RUNTIME_ERROR":
            data["result"] = Result.runtime_error
        elif data["result"] == "MEMORY_LIMIT_EXCEEDED":
            data["result"] = Result.memory_limit_exceeded
        elif data["result"] == "TESTING":
            data["result"] = Result.waiting
        else:
            data["result"] = Result.runtime_error

        data["info"] = {"result_text": "", "error": None}
        if data["result"] == Result.compile_error:
            e = self.post("https://codeforces.com/data/judgeProtocol",
                          headers={"Referer": "http://codeforces.com/submissions/" + username,
                                   "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                   "X-Csrf-Token": self.token,
                                   "X-Requested-With": "XMLHttpRequest"},
                          cookies=self.cookies,
                          data={"submissionId": s["result"][0]["id"],
                                "csrf_token": self.token})
            self.check_status_code(e)
            data["info"] = {"result_text": "Compilation error", "error": json.loads(e.text)}
        return data
