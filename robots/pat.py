# coding=utf-8
from exceptions import LoginFailed
from robot import Robot


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
        return dict(r.cookies)


p = PATRobot()
print(p.login("virusdefender", "092122302asdf"))
