# coding=utf-8
from .robot import Robot
from .exceptions import LoginFailed


class PATRobot(Robot):
    def login(self, username, password):
        r = self.post("http://www.patest.cn/users/sign_in",
                      data={"utf8": "✓",
                            "user[handle]": username,
                            "user[password]": password,
                            "user[remember_me]": 1,
                            "commit": "登录"},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Referer": "http://www.patest.cn/users/sign_in"})
        if r.status_code != 302:
            raise LoginFailed()
        print(123)
        return dict(r.cookies)
