# coding=utf-8
import re
import urllib
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed
from .utils import LANGUAGE


class PATRobot(Robot):
    def __init__(self):
        super().__init__()
        self.token = ""

    def check_url(self, url):
        regex = r"^http://www.patest.cn/contests/pat-(a|b|t)-practise/1\d{3}$"
        return re.compile(regex).match(url) is not None

    def _get_token(self):
        r = self.get("http://www.patest.cn/contests", cookies=self.cookies)
        self.token = re.compile(r"<meta content=\"(.*)\" name=\"csrf-token\" />").findall(r.text)[0]

    def login(self, username, password):

        r = self.post("http://www.patest.cn/users/sign_in",
                      data={"utf8": "✓",
                            "user[handle]": username,
                            "user[password]": password,
                            "user[remember_me]": 1,
                            "commit": "登录"},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": "http://www.patest.cn/users/sign_in"})
        # 登陆成功会重定向到首页,否则200返回错误页面
        if r.status_code != 302:
            raise AuthFailed()

        self.cookies = dict(r.cookies)
        self._get_token()

    @property
    def is_logged_in(self):
        print(self.cookies)
        r = self.get("http://www.patest.cn/users/edit", cookies=self.cookies)
        # 登录状态是200,否则302到登陆页面
        return r.status_code == 200

    def get_problem(self, url):
        if not self.check_url(url):
            raise RequestFailed("Invalid PAT url")
        problem_id = "pat-" + "-".join(re.compile(r"^http://www.patest.cn/contests/pat-(a|b|t)-practise/(\d{4})$").findall(url)[0])
        regex = {"title": r"<div id=\"body\" class=\"span-22 last\">\s*<h1>(.*)</h1>",
                 "time_limit": r"<div class='key'>\s*时间限制\s*</div>\s*<div class='value'>\s*(\d+) ms",
                 "memory_limit": r"<div class='key'>\s*内存限制\s*</div>\s*<div class='value'>\s*(\d+) kB",
                 "description": r"<div id='problemContent'>([\s\S]*?)<b>\s*(?:Input|Input Specification:|输入格式：)\s*</b",
                 "input_description": r"<b>\s*(?:Input|Input Specification:|输入格式：)\s*</b>([\s\S]*?)<b>\s*(?:Output|Output Specification:|输出格式：)\s*</b>",
                 "output_description": r"<b>\s*(?:Output|Output Specification:|输出格式：)\s*</b>([\s\S]*?)<b>\s*(?:Sample Input|输入样例).*</b>",
                 "samples": r"<b>\s*(?:Sample Input|输入样例)\s*(?P<t_id>\d?).?</b>\s*<pre>([\s\S]*?)</pre>\s+<b>(?:Sample Output|输出样例)\s?(?P=t_id).?</b>\s*<pre>([\s\S]*?)</pre>"}
        data = self._regex_page(url, regex)
        data["id"] = problem_id
        return data

    def _regex_page(self, url, regex):
        r = self.get(url)
        if r.status_code != 200:
            raise RequestFailed("Invalid status code [%d] when fetching url [%s]" % (r.status_code, url))
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                raise RegexError("No such data")
            if k != "samples":
                data[k] = self._clean_html_tag(items[0])
            else:
                tmp = []
                for item in items:
                    tmp.append({"input": self._clean_html_tag(item[1]), "output": self._clean_html_tag(item[2])})
                data[k] = tmp
        return data

    def submit(self, url, language, code):
        if language == LANGUAGE.C:
            language = "3"
        elif language == LANGUAGE.CPP:
            language = "2"
        else:
            language = "10"
        r = self.post(url, data={"utf8": "✓", "compiler_id": language, "code": code,
                                 "authenticity_token": self.token},
                      cookies=self.cookies,
                      headers={"Referer": "http://www.patest.cn/",
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 302:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (url, r.status_code))
        return str(re.compile("http://www.patest.cn/submissions/(\d+)").findall(r.headers["Location"])[0])

