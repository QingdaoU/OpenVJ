# coding=utf-8
import re
import html
from .robot import Robot
from .exceptions import AuthFailed,RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language


class ZOJRobot(Robot):

    def check_url(self, url):
        regex = r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=(\d{4})$"
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
        regex = r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=(\d{4})$"
        problem_id = re.compile(regex).findall(url)[0]
        regex = {
                "title": r"<center><span\s*class=\"bigProblemTitle\">(.*)</span></center>",
                "time_Limit": r"<font\s*color=\"green\">Time\s*Limit:\s*</font>\s*(\d+)\s*Seconds",
                "memory_limit": r"<font\s*color=\"green\">Memory\s*Limit:\s*</font>\s*(\d+)\s*KB",
                "description": r"</center>\s*<hr>\s*([\s\S]*?)\s*(?:<b>|<h4>)Input",
                "input_description": r"(?:<h4>|<b>|<strong>)Input(?:</h4>|</b>|</strong>)\s*([\s\S]*?)\s*(?:<h4>|<b>|<strong>)Output(?:</h4>|</b>|</strong>)",
                "output_description": r"(?:<h4>|<b>|<strong>)Output(?:</h4>|</b>|</strong>)\s*([\s\S]*?)\s*(?:<h4>|<b>|<strong>)Sample Input",
                "samples": r"(?:<h4>|<b>|<strong>)Sample Input(?:</h4>|</b>|</strong>)\s*<pre>([\s\S]*?)</pre>\s*(?:<h4>|<strong>|<b>)Sample Output(?:</b>|</strong>|</h4>)\s*<pre>([\s\S]*?)</pre>"
        }
        data = self._regex_page(url, regex)
        data["id"]= problem_id

    def _regex_page(self, url, regex):
        r = self.get(url)
        self.check_status_code(r)
        data = {}
        for k,v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                print(k)
                raise RegexError("NO such data!")
            if k != "samples":
                data[k] = self._clean_html(items[0])
            else :
                data[k] = {"items[0][0]": items[0][1]}
        return data

    def submit(self, submit_url, language, code, orginal_id):
        if(self.is_logged_in() == False):
            raise AuthFailed("Not login!")
        if language == Language.C:
            compiler_id = "1"
        elif language == Language.CPP:
            compiler_id = "2"
        else:
            compiler_id = "4"
        r = self.post(submit_url, data={"problemId": orginal_id, "languageId": compiler_id, "source": code},
                      cookies=self.cookies,
                      headers={"Referer": "http://acm.zju.edu.cn/",
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 200:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (submit_url, r.status_code))
        return str(re.compile(r"<p>Your source has been submitted. The submission id is <font color='red'>(\d+)</font>").findall(r.text)[0])

    def get_result(self, submission_id):
        pass