# coding=utf-8
import re
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


class PATRobot(Robot):
    def __init__(self, cookies=None):
        super().__init__(cookies=cookies)
        self.token = ""

    def check_url(self, url):
        regex = r"^https://www.patest.cn/contests/pat-(a|b|t)-practise/1\d{3}$"
        return re.compile(regex).match(url) is not None

    def _get_token(self):
        r = self.get("https://www.patest.cn/contests", cookies=self.cookies)
        self.check_status_code(r)
        self.token = re.compile(r"<meta content=\"(.*)\" name=\"csrf-token\" />").findall(r.text)[0]

    def login(self, username, password):
        r = self.post("https://www.patest.cn/users/sign_in",
                      data={"utf8": "✓",
                            "user[handle]": username,
                            "user[password]": password,
                            "user[remember_me]": 1,
                            "commit": "登录"},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": "https://www.patest.cn/users/sign_in"})
        # 登陆成功会重定向到首页,否则200返回错误页面
        if r.status_code != 302:
            raise AuthFailed("Failed to login PAT")

        self.cookies = dict(r.cookies)
        self._get_token()

    @property
    def is_logged_in(self):
        r = self.get("http://www.patest.cn/users/edit", cookies=self.cookies)
        # 登录状态是200,否则302到登陆页面
        return r.status_code == 200

    def get_problem(self, url):
        if not self.check_url(url):
            raise RequestFailed("Invalid PAT url")
        problem_id = "pat-" + "-".join(re.compile(r"^https://www.patest.cn/contests/pat-(a|b|t)-practise/(\d{4})$").findall(url)[0])
        regex = {"title": r"<div id=\"body\" class=\"span-22 last\">\s*<h1>(.*)</h1>",
                 "time_limit": r"<div class='key'>\s*时间限制\s*</div>\s*<div class='value'>\s*(\d+) ms",
                 "memory_limit": r"<div class='key'>\s*内存限制\s*</div>\s*<div class='value'>\s*(\d+) kB",
                 "description": r"<div id='problemContent'>([\s\S]*?)<b>\s*(?:Input|Input Specification:|输入格式：)\s*</b",
                 "input_description": r"<b>\s*(?:Input|Input Specification:|输入格式：)\s*</b>([\s\S]*?)<b>\s*(?:Output|Output Specification:|输出格式：)\s*</b>",
                 "output_description": r"<b>\s*(?:Output|Output Specification:|输出格式：)\s*</b>([\s\S]*?)<b>\s*(?:Sample Input|输入样例).*</b>",
                 "samples": r"<b>\s*(?:Sample Input|输入样例)\s*(?P<t_id>\d?).?</b>\s*<pre>([\s\S]*?)</pre>\s+<b>(?:Sample Output|输出样例)\s?(?P=t_id).?</b>\s*<pre>([\s\S]*?)</pre>",
                 "submit_url": r"<form accept-charset=\"UTF-8\" action=\"([\s\S]*?)\" method=\"post\">"}
        data = self._regex_page(url, regex)
        data["id"] = problem_id
        data["submit_url"] = "https://www.patest.cn" + data["submit_url"]
        return data

    def _regex_page(self, url, regex):
        r = self.get(url, cookies=self.cookies, headers={"Referer": "https://www/patest.cn"})
        self.check_status_code(r)
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                raise RegexError("No such data")
            if k != "samples":
                data[k] = self._clean_html(items[0])
            else:
                tmp = []
                for item in items:
                    tmp.append({"input": self._clean_html(item[1]), "output": self._clean_html(item[2])})
                data[k] = tmp
        return data

    def submit(self, submit_url, language, code, *args):
        if language == Language.C:
            compiler_id = "3"
        elif language == Language.CPP:
            compiler_id = "2"
        else:
            compiler_id = "10"
        r = self.post(submit_url, data={"utf8": "✓", "compiler_id": compiler_id, "code": code,
                                        "authenticity_token": self.token},
                      cookies=self.cookies,
                      headers={"Referer": "https://www.patest.cn/",
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 302:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (submit_url, r.status_code))
        return str(re.compile(r"//www.patest.cn/submissions/(\d+)").findall(r.headers["Location"])[0])

    def get_result(self, submission_id, *args):
        r = self.get("https://www.patest.cn/submissions/" + submission_id,
                     cookies=self.cookies,
                     headers={"Referer": "https://www.patest.cn/"})
        self.check_status_code(r)
        data = re.compile(r"<td>\s*<span class='submitRes-(\d+)'>\s*<a[\s\S]*?>([\s\S]*?)</a>\s*</span>\s*</td>\s*"
                          r"<td>[\s\S]*?</td>\s*"
                          r"<td>[\s\S]*?</td>\s*"
                          r"<td>[\s\S]*?</td>\s*"
                          r"<td>(\d*)</td>\s*"
                          r"<td>(\d*)</td>").findall(r.text)
        code = int(data[0][0])
        # https://www.patest.cn/help
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
            r = self.get("https://www.patest.cn/submissions/" + submission_id + "/log",
                         cookies=self.cookies,
                         headers={"Referer": "https://www.patest.cn/"})
            self.check_status_code(r)
            error = self._decode_html(re.compile("<pre>([\s\S]*)</pre>").findall(r.text)[0])

        return {"result": result, "cpu_time": cpu_time, "memory": memory,
                "info": {"result_text": self._clean_html(data[0][1]), "error": error}}

