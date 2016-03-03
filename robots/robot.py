# coding=utf-8
import re
import html
import requests
from .exceptions import RequestFailed, RegexError


class Robot(object):
    def __init__(self, cookies=None):
        self.cookies = cookies if cookies is not None else {}

    def check_url(self, url):
        raise NotImplementedError()

    def login(self, username, password):
        raise NotImplementedError()

    @property
    def is_logged_in(self):
        raise NotImplementedError()

    def get_problem(self, url):
        """
        :return: {"id": String(pat-a-1001/hdu-1002), "title": String, "description": String,
                  "input_description": String, "output_description": String,
                  "samples": [{"input": String, "output": String}],
                  "time_limit": Int, "memory_limit": Int}
        """
        raise NotImplementedError()

    def submit(self, url, language, code):
        """
        :param url
        :param language:
        :param code:
        :return: 提交id
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
        """
        return html.unescape(text)

    def get_result(self, submission_id):
        """
        :param submission_id:
        :return: {"result": Result, "cpu_time": Int, "memory": Int}
        """
        raise NotImplementedError()

    def check_status_code(self, response, status_code=200):
        if response.status_code != status_code:
            raise RequestFailed("Invalid status code [%d] when fetching url [%s], expected %d" %
                                (response.status_code, response.url, status_code))

    def _clean_html(self, text):
        # 先去除部分html标记
        p1 = self._decode_html(re.compile(r"<p.*?>|</p>|<b.*?>|</b>|<span.*?>|</span>|<i.*?>|</i>").sub("", text))
        # <br>之类的转换为\n
        p2 = re.compile(r"<br.*>").sub(r"\n", p1)
        return p2
