# coding=utf-8
from robots.pat import PATRobot


p = PATRobot()
# p.cookies = p.login("virusdefender", "092122302asdf")
# print(p.is_logged_in)
for k, v in p.get_problem("http://www.patest.cn/contests/pat-t-practise/1005").items():
    print("[[[", k, "]]]", v)