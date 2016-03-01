# coding=utf-8
import re
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed


class PATRobot(Robot):
    def check_url(self, url):
        regex = "^http://www.patest.cn/contests/pat-(a|b|t)-practise/1\d{3}$"
        return re.compile(regex).match(url) is not None

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
        return dict(r.cookies)

    @property
    def is_logged_in(self):
        print(self.cookies)
        r = self.get("http://www.patest.cn/users/edit", cookies=self.cookies)
        # 登录状态是200,否则302到登陆页面
        return r.status_code == 200

    def get_problem(self, url):
        regex = {"title": r"<div id=\"body\" class=\"span-22 last\">\s*<h1>(.*)</h1>",
                 "time_limit": r"<div class='key'>\s*时间限制\s*</div>\s*<div class='value'>\s*(\d+) ms",
                 "memory_limit": r"<div class='key'>\s*内存限制\s*</div>\s*<div class='value'>\s*(\d+) kB",
                 "description": r"<div id='problemContent'>([\s\S]*?)<b>\s*(?:Input|Input Specification:|输入格式：)\s*</b",
                 "input_description": r"<b>\s*(?:Input|Input Specification:|输入格式：)\s*</b>([\s\S]*?)<b>\s*(?:Output|Output Specification:|输出格式：)\s*</b>",
                 "output_description": r"<b>\s*(?:Output|Output Specification:|输出格式：)\s*</b>([\s\S]*?)<b>\s*(?:Sample Input|输入样例).*</b>",
                 "samples": r"<b>\s*(?:Sample Input|输入样例)\s*(?P<t_id>\d?).?</b>\s*<pre>([\s\S]*?)</pre>\s+<b>(?:Sample Output|输出样例)\s?(?P=t_id).?</b>\s*<pre>([\s\S]*?)</pre>"}
        return self._regex_page(url, regex)

    def _clean_html_tag(self, text):
        return re.compile("<p>|</p>|<b>|</b>|\r|\n").sub("", text)

