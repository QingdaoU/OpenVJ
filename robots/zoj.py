# coding=utf-8
import re
import html
from .robot import Robot
from .exceptions import AuthFailed,RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


class ZOJRobot(Robot):
    def save(self):
        return {"cookies": self.cookies}

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

    @property
    def is_logged_in(self):
        r = self.get("http://acm.zju.edu.cn/onlinejudge/editProfile.do", cookies = self.cookies)
        return r'<td align="right">Confirm Password</td>' in r.text

    def get_problem(self, url):
        if not self.check_url(url):
            raise RequestFailed("Invalid ZOJ URL!")
        regex = {
                "title": r"<center><span\s*class=\"bigProblemTitle\">(.*)</span></center>",
                "time_Limit": r"<font\s*color=\"green\">Time\s*Limit:\s*</font>\s*(\d+)\s*(?:Seconds|Second)",
                "memory_limit": r"<font\s*color=\"green\">Memory\s*Limit:\s*</font>\s*(\d+)\s*KB",
                "description": r"</center>\s*<hr>[\s\S]*?<p>\s*([\s\S]*?)\s*(?:<b>|<h4>)Input",
                "input_description": r"(?:<h4>|<b>|<strong>)Input(?:</h4>|</b>|</strong>)\s*([\s\S]*?)\s*(?:<h4>|<b>|<strong>)Output(?:</h4>|</b>|</strong>)",
                "output_description": r"(?:<h4>|<b>|<strong>)Output(?:</h4>|</b>|</strong>)\s*([\s\S]*?)\s*(?:<h4>|<b>|<strong>)Sample Input",
                "samples": r"(?:<h4>|<b>|<strong>)Sample\sInput(?:</h4>|</b>|</strong>)\s*<pre>\s*([\s\S]*?)</pre>\s*(?:<h4>|<strong>|<b>)Sample Output(?:</b>|</strong>|</h4>)\s*<pre>([\s\S]*?)</pre>",
                "hint": r'(?:<h4>|<b>|<strong>)Hint(?:</h4>|</b>|</strong>)\s*<p>[\s\S]*<hr>'
        }
        data = self._regex_page(url, regex)
        data["id"] = re.compile(r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=(\d{4})$").findall(url)[0]
        return data

    def _regex_page(self, url, regex):
        r = self.get(url)
        self.check_status_code(r)
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                raise RegexError("NO such data!")
            if k != "samples":
                data[k] = self._clean_html(items[0])
            else:
                data[k] = {items[0][0]: items[0][1]}
        return data

    def submit(self, submit_url, language, code, origin_id):
        if language == Language.C:
            compiler_id = "1"
        elif language == Language.CPP:
            compiler_id = "2"
        else:
            compiler_id = "4"
        r = self.post(submit_url,
                      data={"problemId": str(int(origin_id) - 1000), "languageId": compiler_id, "source": code},
                      cookies=self.cookies,
                      headers={"Referer": "http://acm.zju.edu.cn/",
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 200:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (submit_url, r.status_code))
        return re.compile(r"<p>Your source has been submitted. The submission id is <font color='red'>(\d+)</font>").findall(r.text)[0]

    def get_result(self, submission_id, username):
        url = r"http://acm.zju.edu.cn/onlinejudge/showRuns.do?contestId=1&search=true&firstId=-1&lastId=-1&problemCode=&handle=&idStart=" + submission_id+r"&idEnd="+submission_id
        r = self.get(url, headers={r"Referer": r"http://acm.zju.edu.cn/"}, cookies=self.cookies)
        res = {}
        val = {
                "Accepted": 0,
                "Time Limit Exceeded": 2,
                "Memory Limit Exceeded": 3,
                "Compilation Error": 4,
                "Presentation Error": 5,
                "Wrong Answer": 6,
                "Segmentation Fault": 1,
                "Non-zero Exit Code": 1,
                "Floating Point Error": 1,
                "Output Limit Exceeded": 1,
        }
        compile_list = re.compile(r'<a href="/onlinejudge/showJudgeComment\.do\?submissionId=\d+">Compilation Error</a>').findall(r.text)
        if compile_list.__len__() != 0:
            res["result"] = Result.compile_error
            res["cpu_time"] = 0
            res["memory"] = 0
            compile_id = compile_list[0]
            res["info"] = self.get(r"http://acm.zju.edu.cn/onlinejudge/showJudgeComment.do?submissionId="+compile_id, headers={r"Referer": r"http://acm.zju.edu.cn/"}, cookies=self.cookies).text
        elif r"No submission available." in r.text:
            res["result"] = Result.waiting
            res["cpu_time"] = 0
            res["memory"] = 0
            res["info"] = None
        else:
            regex = {
                "result": r'<span class="judgeReply(?:AC|Other)">\s*([\s\S]*?)\s*</span></td>',
                "cpu_time": r'<td class="runTime">(\d+)</td>',
                "memory": r'<td class="runMemory">(\d+)</td>',
            }
            result_str = re.compile(regex["result"]).findall(r.text)[0]
            res["result"] = val[result_str]
            res["cpu_time"] = re.compile(regex["cpu_time"]).findall(r.text)[0]
            res["memory"] = re.compile(regex["memory"]).findall(r.text)[0]
            res["info"] = None
        return res