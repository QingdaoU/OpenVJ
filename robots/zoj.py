# coding=utf-8
import re
import html
import requests
from .exceptions import AuthFailed,RequestFailed, RegexError, SubmitProblemFailed


class Robot(object):
    def __init__(self, cookies=None):
        self.cookies = cookies if cookies is not None else {}

    def check_url(self, url):
        regex = r"^http://acm.zju.edu.cn/onlinejudge/showProblem.do\?problemCode=\d{4}$"
        return re.compile(regex).match(url) is not None;

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
        r = self.post(url, data, headers);
        if r.status_code is not 302:
            raise AuthFailed("Failed to login ZOJ!");
        self.cookies = dict(r.cookies);

    @property
    def is_logged_in(self):
        r = self.post("http://acm.zju.edu.cn/onlinejudge/editProfile.do", self.cookies)
        return r.status_code == 200

    def get_problem(self, url):
        
        raise NotImplementedError()

    def submit(self, url, language, code):
        """
        提交题目
        result和language按照utils中转换一下
        :param url
        :param language:
        :param code:
        :return: 提交id 字符串
        """
        raise NotImplementedError()

    def _request(self, method, url, **kwargs):
        kwargs["timeout"] = 10

        if kwargs["headers"] is None:
            kwargs["headers"] = {}

        cookies = kwargs.pop("cookies")
        if cookies is not None:
            kwargs["headers"]["Cookie"] = ""
            for k, v in cookies.items():
                kwargs["headers"]["Cookie"] += (k + "=" + v + "; ")

        common_headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                          "Accept-Encoding": "gzip, deflate",
                          "Accept-Language": "en-US,en;q=0.8,zh;q=0.6,zh-CN;q=0.4",
                          "Cache-Control": "no-cache",
                          "User-Agent": "VirtualJudge"}
        for k, v in common_headers.items():
            if k not in kwargs["headers"]:
                kwargs["headers"][k] = v
        retries = 3
        while True:
            try:
                r = requests.request(method, url, **kwargs)
                if r.status_code >= 400:
                    raSise RequestFailed("Invalid status code [%d] when fetching url [%s]" % (r.status_code, url))
                return r
            except requests.RequestException as e:
                if retries == 0:
                    raise RequestFailed(e)
                retries -= 1

    def get(self, url, headers=None, cookies=None, allow_redirects=False):
        return self._request("get", url, cookies=cookies, headers=headers, allow_redirects=allow_redirects)

    def post(self, url, data, headers=None, cookies=None, allow_redirects=False):
        return self._request("post", url, data=data, cookies=cookies, headers=headers, allow_redirects=allow_redirects)

    def _decode_html(self, text):
        """
        html实体编码的解码
        比如 &gt -> >  &lt -> <
        """
        return html.unescape(text)

    def get_result(self, submission_id):
        """
        获取提交结果
        result和language按照utils中转换一下
        返回值中info["error"]只有编译错误的时候才会为字符串,否则为None
        :param submission_id:
        :return: {"result": Result, "cpu_time": Int, "memory": Int, "info": {"error": None/String}}
        """
        raise NotImplementedError()

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
