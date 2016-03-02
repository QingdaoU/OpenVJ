# coding=utf-8
import re
import urllib
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


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
            raise AuthFailed("Failed to login PAT")

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
        if language == Language.C:
            compiler_id = "3"
        elif language == Language.CPP:
            compiler_id = "2"
        else:
            compiler_id = "10"
        r = self.post(url, data={"utf8": "✓", "compiler_id": compiler_id, "code": code,
                                 "authenticity_token": self.token},
                      cookies=self.cookies,
                      headers={"Referer": "http://www.patest.cn/",
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 302:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (url, r.status_code))
        return str(re.compile(r"http://www.patest.cn/submissions/(\d+)").findall(r.headers["Location"])[0])

    def get_result(self, submission_id):
        r = self.get("http://www.patest.cn/submissions/" + submission_id,
                     cookies=self.cookies,
                     headers={"Referer": "http://www.patest.cn/"})
        if r.status_code != 200:
            raise RequestFailed("Failed to get submission result, submission id: %s, status code: %d" % (submission_id, r.status_code))
        data = re.compile(r"<td>\s*<span class='submitRes-(\d+)'>\s*<a[\s\S]*?>([\s\S]*?)</a>\s*</span>\s*</td>\s*"
                          r"<td>[\s\S]*?</td>\s*"
                          r"<td>[\s\S]*?</td>\s*"
                          r"<td>[\s\S]*?</td>\s*"
                          r"<td>(\d*)</td>\s*"
                          r"<td>(\d*)</td>").findall(r.text)
        code = int(data[0][0])
        # http://www.patest.cn/help
        # 等待评测 正在评测
        if code in [0, 1]:
            result = Result.waiting
        # 编译错误
        elif code == 2:
            result = Result.compile_error
        # 答案正确
        elif code == 3:
            result = Result.accepted
        # 部分正确 答案错误
        elif code == [4, 6]:
            result = Result.wrong_answer
        # 格式错误
        elif code == 5:
            result = Result.format_error
        # 运行超时
        elif code == 7:
            result = Result.time_limit_exceeded
        # 内存超限
        elif code == 8:
            result = Result.memory_limit_exceeded
        #内部错误
        elif code == 14:
            result = Result.system_error
        # 返回非0 异常退出 段错误 浮点错误 多种错误
        else:
            result = Result.runtime_error

        if data[0][2]:
            cpu_time = int(data[0][2])
        else:
            cpu_time = None
        if data[0][3]:
            memory = int(data[0][3])
        else:
            memory = None

        error = None
        if result == Result.compile_error:
            r = self.get("http://www.patest.cn/submissions/" + submission_id + "/log",
                         cookies=self.cookies,
                         headers={"Referer": "http://www.patest.cn/"})
            if r.status_code != 200:
                raise RequestFailed("Failed to get submission error info, submission id: %s, status code: %d" %
                                    (submission_id, r.status_code))
            print(r.text)
            error = re.compile("<pre>([\s\S]*)</pre>").findall(r.text)[0]

        return {"result": result, "cpu_time": cpu_time, "memory": memory,
                "info": {"result_text": self._clean_html_tag(data[0][1]), "error": error}}
