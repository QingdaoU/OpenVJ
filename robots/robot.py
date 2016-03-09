# coding=utf-8
import re
import html
import requests
from .exceptions import RequestFailed, RegexError


class Robot(object):
    def __init__(self, cookies=None):
        self.cookies = cookies if cookies is not None else {}

    def save(self):
        raise NotImplementedError()

    def check_url(self, url):
        """
        检查一个url是否是本oj的合法的url
        :param url:
        :return: True/False
        """
        raise NotImplementedError()

    def login(self, username, password):
        """
        使用给定的用户名和密码登录系统 然后更新self.cookies
        :param username:
        :param password:
        :return: None
        """
        raise NotImplementedError()

    @property
    def is_logged_in(self):
        """
        使用当前的cookies 检查是否是登录状态
        :return: True/False
        """
        raise NotImplementedError()

    def get_problem(self, url):
        """
        获取url上的题目信息
        cpu为毫秒 内存单位是M
        :return: {"id": String(pat-a-1001/hdu-1002), "title": String, "description": String,
                  "input_description": String, "output_description": String,
                  "submit_url: String/URL,
                  "samples": [{"input": String, "output": String}],
                  "spj": True/False,
                  "time_limit": Int ms, 
                  "memory_limit": Int M,
                  "hint": String/None}
        """
        raise NotImplementedError()

    def submit(self, submit_url, language, code, origin_id):
        """
        提交题目
        result和language按照utils中转换一下
        :param submit_url
        :param language:
        :param code:
        :param origin_id: 题目的原始id
        :return: 提交 id 字符串 hduoj返回None
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
                    raise RequestFailed("Invalid status code [%d] when fetching url [%s]" % (r.status_code, url))
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

    def get_result(self, submission_id, username):
        """
        获取提交结果
        result和language按照utils中转换一下
        返回值中info["error"]只有编译错误的时候才会为字符串,否则为None
        :param submission_id:
        :param username: 提交这个题的用户名
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

    def _clean_html(self, text):
        # 先去除部分html标记
        p1 = self._decode_html(re.compile(r"<p.*?>|</p>|<b.*?>|</b>|<span.*?>|</span>").sub("", text))
        # <br>之类的转换为\n
        p2 = re.compile(r"<br.*>").sub(r"\n", p1)
        return p2
