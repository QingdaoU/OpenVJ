# coding=utf-8
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from celery import states


from .serializers import ProblemSerializer
from .models import OJ, Problem, RobotUser, RobotStatusInfo, ProblemStatus
from .tasks import get_problem


def error_response(error_reason):
    return Response(data={"code": 1, "data": error_reason})


def serializer_invalid_response(serializer):
    for k, v in serializer.errors.iteritems():
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
            if problem.status == ProblemStatus.done:
                return success_response(ProblemSerializer(problem).data)
            elif problem.status == ProblemStatus.crawling:
                task = get_problem.AsyncResult(problem.task_id)
                if task.state == states.SUCCESS:
                    result = task.get()
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
                elif task.state == states.FAILURE:
                    problem.status = ProblemStatus.failed
                    problem.save()
                    return success_response({"status": ProblemStatus.failed})
            elif problem.status == ProblemStatus.failed:
                return success_response({"status": ProblemStatus.failed})
        except Problem.DoesNotExist:
            pass
        try:
            oj = OJ.objects.get(name=oj, is_valid=True)
        except OJ.DoesNotExist:
            return error_response("不存在该oj")
        robot_status = RobotStatusInfo.objects.filter(robot_user__oj=oj).first()
        if not robot_status:
            return error_response("登录信息错误")
        robot = import_class(oj.robot)(**json.loads(robot_status.status_info))
        if not robot.check_url(url):
            return error_response("url格式错误")
        task_id = get_problem.delay(robot, url).id
        Problem.objects.create(oj=oj, url=url, status=ProblemStatus.crawling, task_id=task_id)
        return success_response({"status": ProblemStatus.crawling})

