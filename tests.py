# coding=utf-8
import unittest
from robots.zoj import ZOJRobot

class mytest(unittest):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def testcheck_url(self):
        self.assertEqual(ZOJRobot.check_url(r"http://acm.zju.edu.cn/onlinejudge/showProblem.do?problemCode=1234"), True);

if(__name__ == '__main__'):
    unittest.main();