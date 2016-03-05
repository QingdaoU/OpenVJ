# coding=utf-8
import re
import html
from .robot import Robot
from .exceptions import AuthFailed,RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language


class ZOJRobot(Robot):

    def check_url(self, url):
        regex = r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=\d{4}$"
        return re.compile(regex).match(url) is not None

    def login(self, username, password):
        url = r"http://acm.zju.edu.cn/onlinejudge/login.do"
        data = {
                "handle": username,
                "password": password,
                "rememberMe": "on"
        }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "http://acm.zju.edu.cn/onlinejudge/login.do"
        }
        r = self.post(url, data, headers)

        if r.status_code != 302:
            raise AuthFailed("Failed to login ZOJ!")
        self.cookies = dict(r.cookies)

    def logout(self):
        self.cookies = None

    @property
    def is_logged_in(self):
        r = self.get("http://acm.zju.edu.cn/onlinejudge/editProfile.do", cookies = self.cookies)
        return r'<td align="right">Confirm Password</td>' in r.text

    def get_problem(self, url):
        if not self.check_url(url):
            raise RequestFailed("Invalid ZOJ URL!")
        regex = r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=\d{4}$"
        problem_id = re.compile(regex).findall(url)[0][0]
        regex = {
                "title": r"<center><span class=\"bigProblemTitle\">.*</span></center>",
                "time_Limit": r"<font color=\"green\">Time Limit: </font> \d+ Seconds",
                "memory_limit": r"<font color=\"green\">Memory Limit: </font> 32768 KB",
                "description": r"",
                "input_description": r"",
                "output_description": r"",
                "samples": r""
        }
        data = self._regex_page(url, regex)
        data.id = problem_id
        return data

    def _regex_page(self, url, regex):
        r = self.get(url)
        self.check_status_code(r)
        data = {}
        for k,v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                raise RegexError("NO such data!")
            if k != "samples":
                data[k] = self._clean_html(items[0])
            else :
                tmp = []
                for item in items:
                    tmp.append({"input": self._clean_html(item[0]), "output": self._clean_html((item[1]))})
                data[k] = tmp
        return data

    def _clean_html(self, text):
        return self._decode_html(re.compile(r"<h4>|</h4>|<p>|</p>|<b>|</b>|\r|\n|<span>|</span>").sub("", text));

    def submit(self, url, language, code):
        if language == Language.C:
            compiler_id = "1"
        elif language == Language.CPP:
            compiler_id = "2"
        else:
            compiler_id = "4"
        regex = r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=\d{4}$"
        problem_id = re.compile(regex).findall(url)[0][0]
        r = self.post(url, data={"problemId": problem_id, "languageId": compiler_id, "source": code},
                      cookies=self.cookies,
                      headers={"Referer": "http://acm.zju.edu.cn/",
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 200:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (url, r.status_code))
        return str(re.compile(r"<p>Your source has been submitted. The submission id is <font color='red'>\d+</font>").findall(r.text)[0][0])

    def _decode_html(self, text):
        """
        html实体编码的解码
        比如 &gt -> >  &lt -> <
        """
        return html.unescape(text)

    def get_result(self, submission_id):
        pass
    def check_status_code(self, response, status_code=200):
        """
        检查响应是否是指定的status code 否则引发异常
        :param response:
        :param status_code:
        :return:
        """
        if response.status_code != status_code:
            raise RequestFailed("Invalid status code [%d] when fetching url [%s], expected %d" %
                                (response.status_code, response.url, status_code))

