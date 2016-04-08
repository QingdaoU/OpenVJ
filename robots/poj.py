# coding=utf-8
import re
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


class PojRobot(Robot):
    def check_url(self, url):
        regex = r"^http://poj.org/problem\?id=[1-9]\d{3}$"
        return re.compile(regex).match(url) is not None

    def login(self, username, password):
        r = self.post("http://poj.org/login",
                      data={"user_id1": username,
                            "password1": password,
                            "B1": "login",
                            "url": "/"},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": "http://poj.org/"})

        # 登陆成功会重定向到首页,否则200返回错误页面
        if r.status_code != 302:
            raise AuthFailed("Failed to login Poj")
        self.cookies = dict(r.cookies)

    @property
    def is_logged_in(self):
        r = self.get("http://poj.org/mail", cookies=self.cookies)
        # 登录状态是200,否则302到登陆页面
        return r.status_code == 200

    def get_problem(self, url):
        if not self.check_url(url):
            raise RequestFailed("Invalid Poj url")
        regex = {"title": r"ptt\" lang=\"en-US\"\>([\s\S]*?)</div>",
                 "time_limit": r"Time Limit:</b>\s*(\d+)MS",
                 "memory_limit": r"Memory Limit:</b>\s*(\d+)K",
                 "description": r"Description</p><div class=\"ptx\" lang=\"en-US\">([\s\S]*?)(?=</div)",
                 "input_description": r"Input</p><div class=\"ptx\" lang=\"en-US\">([\s\S]*?)(?=</div)",
                 "output_description": r"Output</p><div class=\"ptx\" lang=\"en-US\">([\s\S]*?)(?=</div)",
                 "spj": r'<td style="font-weight:bold; color:red;">Special Judge</td>',
                 "hint": r'Hint</p><div class="ptx" lang="en-US">([\s\S]*?)<p class="pst">',
                 "samples": r'Sample Input</p><pre class="sio">([\s\S]*?)</pre>'
                            r'<p class="pst">Sample Output</p><pre class="sio">([\s\S]*?)</pre><p class="pst">'
                 }
        problem_id = re.compile(r"\d{4}").search(url).group()
        data = self._regex_page(url, regex)
        data["problem_id"] = problem_id
        data["submit_url"] = "http://poj.org/submit"
        return data

    def _clean_html(self, text):
        return self._decode_html(re.compile("<p>|</p>|<b>|</b>|\r|\n|<span>|</span>").sub("", text))

    def _regex_page(self, url, regex):
        r = self.get(url)
        self.check_status_code(r)
        data = {}
        for k, v in regex.items():
            items = re.compile(v).findall(r.text)
            if not items:
                if k == "spj":
                    data[k] = False
                elif k == "hint":
                    data[k] = None
                else:
                    raise RegexError("No such data")
            if k == "samples":
                data[k] = [{"input": items[0][0], "output": items[0][1]}]
            elif items:
                if k == "spj":
                    data[k] = True
                else:
                    data[k] = self._clean_html(items[0])
        data["memory_limit"] = int(data["memory_limit"]) // 1024
        return data

    def submit(self, submit_url, language, code, origin_id):
        if language == Language.C:
            language = "1"
        elif language == Language.CPP:
            language = "0"
        else:
            language = "2"

        r = self.post(submit_url, data={"problem_id": origin_id,
                                        "language": language,
                                        "source": code,
                                        "submit": "Submit",
                                        "encoded": 0},
                      cookies=self.cookies,
                      headers={"Referer": "http://poj.org/submit?problem_id="+str(origin_id),
                               "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 302:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code: %d" % (submit_url, r.status_code))

    def get_result(self, submission_id, username):
        status_url = "http://poj.org/status?user_id=" + username
        r = self.get(status_url, headers={"Refer": status_url})
        self.check_status_code(r)

        data = re.compile(r"(\d+)</td><td><a href=userstatus\?user_id=(?:[\s\S]*?)"
                          r"<font color=(?:.*?)>([\s\S]*?)</font>").findall(r.text)

        submission_id = data[0][0]
        code = data[0][1]

        if code == "Accepted":
            result = Result.accepted
        elif code in ["Queuing", "Compiling", "Running"]:
            result = Result.waiting
        elif code == "Presentation Error":
            result = Result.format_error
        elif code == "Wrong Answer":
            result = Result.wrong_answer
        elif code == "Runtime Error":
            result = Result.runtime_error
        elif code == "Time Limit Exceeded":
            result = Result.time_limit_exceeded
        elif code == "Memory Limit Exceeded":
            result = Result.memory_limit_exceeded
        elif code == "Output Limit Exceeded":
            result = Result.runtime_error
        elif code == "Compile Error":
            result = Result.compile_error
        elif code == "System Error":
            result = Result.system_error
        else:
            result = Result.runtime_error

        if code == "Accepted":
            r = re.compile(r"<font color=blue>Accepted</font></td><td>(\d+)K</td><td>(\d+)MS</td>").findall(r.text)
            memory = r[0][0]
            cpu_time = r[0][1]
        else:
            cpu_time = memory = None

        error = None
        if result == Result.compile_error:
            r = self.get(r"http://poj.org/showcompileinfo?solution_id=" + str(submission_id),
                         headers={"Referer": "http://poj.org/status?user_id=" + username})
            self.check_status_code(r)
            error = self._clean_html(str(re.compile("<pre>([\s\S]*)</pre>").findall(r.text)))

        return {"result": result, "cpu_time": cpu_time, "memory": memory,
                "info": {"result_text": self._clean_html(data[0][1])}, "error": error}
