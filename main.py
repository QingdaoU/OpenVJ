# coding=utf-8
import time
from robots.pat import PATRobot
from robots.utils import Language


p = PATRobot()
p.login("virusdefender", "092122302asdf")
# print(p.is_logged_in)
# for i in range(10, 50):
#     print(i)
#     for k, v in p.get_problem("http://www.patest.cn/contests/pat-b-practise/10" + str(i)).items():
#         print("[[[", k, "]]]", v)
#     time.sleep(3)
# p.get_token()
#id = p.submit("http://www.patest.cn/contests/32/1001/submit", language=Language.C, code="123")
print(p.get_result("1680150"))