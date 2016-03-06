# coding=utf-8
import unittest
from robots.zoj import ZOJRobot
from robots.pat import PATRobot
from robots.utils import Language
class ZOJRobotTest(unittest.TestCase):

    def setUp(self):
        self.tclass = ZOJRobot()
        self.tclass.login("ltwy", "jiangxuelei")

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
        self.assertEquals(self.tclass.is_logged_in, True)


    def test_get_problem(self):
        self.tclass.get_problem(r"http://acm.zju.edu.cn/onlinejudge/showProblem.do?problemCode=3807")

    def test_submit(self):
        print(self.tclass.submit(r"http://acm.zju.edu.cn/onlinejudge/submit.do?problemId=1", Language.CPP, r'#include<stdio.h> int main(){ int a,b; scanf("%d %d",&a,&b); printf("%d\n",a+b);return 0;}', int("1001") - 1000))

    def test_get_result(self):
        self.tclass.get_result("4162525", "ltwy")

