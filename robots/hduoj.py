# coding=utf-8
import re
from .robot import Robot
from .exceptions import AuthFailed, RequestFailed, RegexError, SubmitProblemFailed
from .utils import Language, Result


class HduojRobot(Robot):
    def check_url(self, url):
        regex = r"^http://acm.hdu.edu.cn/showproblem.php\?pid=\d{4}$"
        return re.compile(regex).match(url) is not None

    def login(self, username, password):
        r = self.post("http://acm.hdu.edu.cn/userloginex.php?action=login",
                      data={"username": username,
                            "userpass": password,
                            "login": "Sign In"},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": "http://acm.hdu.edu.cn/"})
        # 登陆成功会重定向到首页,否则200返回错误页面
        if r.status_code != 302:
            raise AuthFailed("Failed to login Hduoj")

        self.cookies = dict(r.cookies)

    @property
    def is_logged_in(self):
        r = self.get("http://acm.hdu.edu.cn/control_panel.php", cookies=self.cookies)
        # 登录状态是200,否则302到登陆页面
        return r.status_code == 200

    def get(self, url, headers=None, cookies=None, allow_redirects=False):
        r = super().get(url, headers=headers, cookies=cookies, allow_redirects=allow_redirects)
        r.encoding = "gb2312"
        return r

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
                    data["hint"] = None
                else:
                    raise RegexError("No such data")
            if k == "samples":
                data[k] = [{"input": items[0], "output": items[1]}]
            elif items:
                if k == "spj":
                    data[k] = True
                else:
                    data[k] = self._clean_html(items[0])
        data["memory_limit"] = int(data["memory_limit"]) // 1024
        data["time_limit"] = int(data["time_limit"])

        return data

    def get_problem(self, url):
        if not self.check_url(url):
            raise RequestFailed("Invaild Hduoj url")
        regex = {"title": r"<h1 style='color:#1A5CC8'>(.*)</h1>",
                 "time_limit": r"Time Limit:\s*[\d]*/([\d]*)\s*MS",
                 "memory_limit": r"Memory Limit:\s*[\d]*/([\d]*)\s*K",
                 "description": r"Problem Description</div>\s*<div class=panel_content>([\s\S]*?)</div>",
                 "input_description": r"Input</div>\s*<div class=panel_content>([\s\S]*?)</div>",
                 "output_description": r"Output</div>\s*<div class=panel_content>([\s\S]*?)</div>",
                 "hint": r"Hint(?:[\s\S]*?Hint[\s\S]*?</i>|</i>\s*</div>)([\s\S]*?)</div>",
                 "spj": r"<font color=red>Special Judge</font>",
                 "samples": r'Courier New,Courier,monospace;">([\s\S]*?)(?:<div|</div>)'}
        problem_id = re.compile(r"\d{4}").search(url).group()
        data = self._regex_page(url, regex)
        data["problem_id"] = problem_id
        data["submit_url"] = "http://acm.hdu.edu.cn/submit.php?action=submit"
        return data

    def submit(self, submit_url, language, code, origin_id):
        code = code.encode("gb2312")
        if language == Language.C:
            language = "1"
        elif language == Language.CPP:
            language = "0"
        else:
            language = "5"

        r = self.post(submit_url, data={"check": "0", "problemid": origin_id,
                                        "language": language,
                                        "usercode": code},
                      cookies=self.cookies,
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": submit_url})

        if r.status_code != 302:
            raise SubmitProblemFailed("Failed to submit problem, url: %s, status code %d" % (submit_url, r.status_code))

    def get_result(self, submission_id, username):
        status_url = r"http://acm.hdu.edu.cn/status.php?&user=" + username
        r = self.get(status_url,
                     headers={"Refer": status_url})
        self.check_status_code(r)

        data = re.compile(r"(\d+)</td><td>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:[\s\S]*?)>"
                          r"<font[\s\S]*?>(.*?)</font>[\s\S]*?(\d*)MS</td><td>(\d*)K").findall(r.text)

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
        elif code == "Compilation Error":
            result = Result.compile_error
        elif code == "System Error":
            result = Result.system_error
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
            r = self.get(r"http://acm.hdu.edu.cn/viewerror.php?rid=" + submission_id,
                         headers={"Referer": "http://acm.hdu.edu.cn/status.php?first=&pid=&lang=0&status=0&user=" + username})
            self.check_status_code(r)
            error = self._clean_html(str(re.compile("<pre>([\s\S]*)</pre>").findall(r.text)))

        return {"result": result, "cpu_time": cpu_time, "memory": memory,
                "info": {"result_text": self._clean_html(data[0][1]), "error": error}}

