# coding=utf-8
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from celery import states


from .serializers import ProblemSerializer, CreateSubmissionSerializer
from .models import OJ, Problem, RobotUser, RobotStatusInfo, ProblemStatus
from .tasks import get_problem


def error_response(error_reason):
    return Response(data={"code": 1, "data": error_reason})


def serializer_invalid_response(serializer):
    for k, v in serializer.errors.items():
        return error_response(k + " : " + v[0])


def success_response(data):
    return Response(data={"code": 0, "data": data})


def import_class(cl):
    d = cl.rfind(".")
    class_name = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [class_name])
    return getattr(m, class_name)


class ProblemAPIView(APIView):
    def get(self, request):
        oj = request.GET.get("oj")
        url = request.GET.get("url")
        if not (oj and url):
            return error_response("参数错误")
        try:
            problem = Problem.objects.get(url=url, is_valid=True)
            # 如果已经爬取完成,就直接返回数据库中的结果
            if problem.status == ProblemStatus.done:
                return success_response(ProblemSerializer(problem).data)
            # 如果还是正在爬取的状态,说明已经提交过任务的了,需要获取一下任务状态
            elif problem.status == ProblemStatus.crawling:
                task = get_problem.AsyncResult(problem.task_id)
                # 如果任务状态是成功,就更新数据库,并返回结果
                if task.state == states.SUCCESS:
                    result = task.get()
                    problem.origin_id = result["id"]
                    problem.title = result["title"]
                    problem.submit_url = result["submit_url"]
                    problem.description = result["description"]
                    problem.time_limit = result["time_limit"]
                    problem.memory_limit = result["memory_limit"]
                    problem.input_description = result["input_description"]
                    problem.output_description = result["output_description"]
                    problem.samples = json.dumps(result["samples"])
                    problem.status = ProblemStatus.done
                    problem.save()
                    return success_response(ProblemSerializer(problem).data)
                # 如果任务状态是失败,返回失败结果
                elif task.state == states.FAILURE:
                    problem.status = ProblemStatus.failed
                    problem.save()
                    return success_response({"status": ProblemStatus.failed})
                else:
                    return success_response({"status": ProblemStatus.crawling})
            elif problem.status == ProblemStatus.failed:
                return success_response({"status": ProblemStatus.failed})
        except Problem.DoesNotExist:
            pass
        # 题目不存在,需要创建任务
        try:
            oj = OJ.objects.get(name=oj, is_valid=True)
        except OJ.DoesNotExist:
            return error_response("不存在该oj")
        # 找到爬虫的登录信息
        robot_status = RobotStatusInfo.objects.filter(robot_user__oj=oj).first()
        if not robot_status:
            return error_response("登录信息错误")
        # 使用登录信息实例化一个爬虫
        robot = import_class(oj.robot)(**json.loads(robot_status.status_info))
        if not robot.check_url(url):
            return error_response("url格式错误")
        # 创建任务并插入空白题目task_id
        task_id = get_problem.delay(robot, url).id
        Problem.objects.create(oj=oj, url=url, status=ProblemStatus.crawling, task_id=task_id)
        return success_response({"status": ProblemStatus.crawling})


class SubmissionAPIView(APIView):
    def post(self, request):
        serializer = CreateSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            return success_response(serializer.data)
        else:
            return serializer_invalid_response(serializer)