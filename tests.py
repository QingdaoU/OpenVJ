# coding=utf-8
import unittest
from robots.zoj import ZOJRobot
from robots.pat import PATRobot

class ZOJRobotTest(unittest.TestCase):

    def setUp(self):
        self.tclass = ZOJRobot()

    def tearDown(self):
        pass

    def test_check_url(self):
        self.assertEqual(self.tclass.check_url(r"http://acm.zju.edu.cn/onlinejudge/showProblem.do?problemCode=12234"), False)
        self.assertEqual(self.tclass.check_url(r"http://acm.zju.edu.cn/onlinejudge/showProblem.do?problemCode=12"), False)
        self.assertEqual(self.tclass.check_url(r"http://acm.zju.edu.cn/onlinejudge/showProblem.do?problemCode=1234"), True)
        self.assertEqual(self.tclass.check_url(r"http://acm.zju.edu.cn/onlinejudge/showProblem.do?problemCode=1223"), True)

    def test_login(self):
        self.assertEquals(self.tclass.login("ltwy", "jiangxuelei"), None)

    def test_is_logged_in(self):
        self.tclass.login("ltwy", "jiangxuelei")
        self.assertEquals(self.tclass.is_logged_in, True)
        self.tclass.logout()
        self.assertEquals(self.tclass.is_logged_in, False)

