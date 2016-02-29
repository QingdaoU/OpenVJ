# coding=utf-8
import requests


class Robot(object):
    def __init__(self, cookies=None):
        self.cookies = cookies

    def login(self, username, password):
        raise NotImplementedError()

    @property
    def is_logged_in(self):
        raise NotImplementedError()

    def get_problem(self, url):
        raise NotImplementedError()

    def _request(self, method, url, **kwargs):
        kwargs["allow_redirects"] = False
        common_headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                          "Accept-Encoding": "gzip, deflate",
                          "Accept-Language": "en-US,en;q=0.8,zh;q=0.6,zh-CN;q=0.4",
                          "Cache-Control": "no-cache",
                          "User-Agent": "VirtualJudge"}
        for k, v in common_headers.items():
            if k not in kwargs["headers"]:
                kwargs["headers"][k] = v
        return requests.request(method, url, **kwargs)

    def get(self, url, headers=None):
        if headers is None:
            headers = {}
        return self._request("get", url, headers=headers)

    def post(self, url, data, headers=None):
        if headers is None:
            headers = {}
        return self._request("post", url, data=data, headers=headers)
