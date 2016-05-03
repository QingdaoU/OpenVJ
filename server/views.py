# coding=utf-8
import json
import random

from rest_framework.views import APIView
from celery import states

from robots.utils import Result
from .serializers import ProblemSerializer, CreateSubmissionSerializer, SubmissionSerializer
from .models import (OJ, Problem, RobotUser, RobotStatusInfo, ProblemStatus,
                     Submission, APIKey, SubmissionStatus, RobotUserStatus, SubmissionWaitingQueue)
from .tasks import get_problem, submit_dispatcher
from .utils import success_response, error_response, serializer_invalid_response, import_class


demo_key = "977c723a4f93ed311f052e6fad51728b"


class ProblemAPIView(APIView):
    def get(self, request):
        oj = request.GET.get("oj")
        url = request.GET.get("url")
        if not (oj and url):
            return error_response("参数错误")
        try:
            api_key = APIKey.objects.get(api_key=request.META.get("HTTP_APIKEY", demo_key), is_valid=True)
        except APIKey.DoesNotExist:
            return error_response("需要api_key")
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
            return error_response("oj不存在")
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
            data = serializer.data
            try:
                problem = Problem.objects.get(id=data["problem_id"], is_valid=True)
            except Problem.DoesNotExist:
                return error_response("题目不存在")

            oj = problem.oj
            if not oj.is_valid:
                return error_response("oj不存在")

            try:
                api_key = APIKey.objects.get(api_key=request.META.get("HTTP_APIKEY", demo_key), is_valid=True)
            except APIKey.DoesNotExist:
                return error_response("需要api_key")

            submission = Submission.objects.create(api_key=api_key,
                                                   code=data["code"],
                                                   problem=problem,
                                                   language=data["language"],
                                                   result=Result.waiting,
                                                   status=SubmissionStatus.crawling)

            available_robot_users = RobotUser.objects.filter(oj=oj, is_valid=True, status=RobotUserStatus.free)
            if not available_robot_users.exists():
                SubmissionWaitingQueue.objects.create(submission=submission)
            else:
                # 占用用户
                robot_user = available_robot_users[random.randint(0, available_robot_users.count() - 1)]
                robot_user.status = RobotUserStatus.occupied
                robot_user.save()

                # 根据用户查询登录信息并实例化相关的类
                robot_status = RobotStatusInfo.objects.get(robot_user=robot_user)
                robot = import_class(problem.oj.robot)(**json.loads(robot_status.status_info))

                task_id = submit_dispatcher.delay(problem, submission, robot_user, robot).id
                submission.task_id = task_id
                submission.save(update_fields=["task_id"])
            return success_response({"submission_id": submission.id})
        else:
            return serializer_invalid_response(serializer)

    def get(self, request):
        submission_id = request.GET.get("submission_id")
        if not submission_id:
            return error_response("参数错误")
        submission = Submission.objects.get(id=submission_id)
        return success_response(SubmissionSerializer(submission).data)