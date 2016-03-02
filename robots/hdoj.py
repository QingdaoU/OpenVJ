# coding=utf-8
import re
import requests
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed


class HDOJRobot(Robot):
    def check_url(self, url):
        regex = "^http://acm.hdu.edu.cn/showproblem.php?pid=\d{4}$"
        return re.compile(regex).match(url) is not None

    def login(self, username, password):
        r = self.post("http://acm.hdu.edu.cn/userloginex.php?action=login",
                      data={"user[handle]": username,
                            "user[password]": password,
                            "login": "Sign In"},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": "http://acm.hdu.edu.cn/"})
        # 登陆成功会重定向到首页,否则200返回错误页面
        if r.status_code != 302:
            raise AuthFailed()
        return dict(r.cookies)

    @property
    def is_logged_in(self):
        print(self.cookies)
        r = self.get("http://acm.hdu.edu.cn/control_panel.php", cookies=self.cookies)
        # 登录状态是200,否则302到登陆页面
        return r.status_code == 200

    def get(self, url, headers=None, cookies=None, allow_redirects=False):
        r = super().get(url, headers=headers, cookies=cookies, allow_redirects=allow_redirects)
        r.encoding = "gb2312"
        return r

    def post(self, url, data, headers=None, cookies=None, allow_redirects=False):
        return self._request("post", url, data=data, cookies=cookies, headers=headers, allow_redirects=allow_redirects)

    def _regex_page(self, url, regex):
        r = self.get(url)
        self.check_status_code(r)
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                raise RegexError("No such data")
            if k == "samples":
                data[k] = [{"input": items[0], "output": items[1]}]
            else:
                data[k] = items[0]
        print(data["samples"])
        return data


    def get_problem(self, url):
        regex = {"title": r"<h1 style='color:#1A5CC8'>(.*)</h1>",
                 "time_limit": r"Time Limit:\s*[\d]*/([\d]*) MS",
                 "memory_limit": r"Memory Limit:\s*[\d]*/([\d]*) K",
                 "description": r"Problem Description</div> <div class=panel_content>([\s\S]*?)</div>",
                 "input_description": r"Input</div> <div class=panel_content>([\s\S]*?)</div>",
                 "output_description": r"Output</div> <div class=panel_content>([\s\S]*?)</div>",
                 "samples": r"Courier New,Courier,monospace;\">([\s\S]*?)</div>"
                 }
        return self._regex_page(url, regex)

