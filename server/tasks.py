# coding=utf-8
from __future__ import absolute_import
import time
import json

from openvj import celery_app
from robots.utils import Result
from .models import RobotUserStatus, SubmissionStatus, SubmissionWaitingQueue


# remote robot task
@celery_app.task
def get_problem(robot, url):
    return robot.get_problem(url)


# remote robot task
@celery_app.task
def submit(robot, robot_user, submit_url, origin_id, language, code):
    try:
        origin_submission_id = robot.submit(submit_url, language, code, origin_id)
    except Exception as e:
        return {"result": Result.system_error, "cpu_time": None, "memory": None,
                "info": {"error": "Failed to submit problem, error: " + str(e)},
                "origin_submission_id": None}
    # 2秒后执行
    time.sleep(2)
    retries = 20
    while retries:
        try:
            result = robot.get_result(origin_submission_id, robot_user.username)
        except Exception as e:
            return {"result": Result.system_error, "cpu_time": None, "memory": None,
                    "info": {"error": "Failed to get submission result, error: " + str(e)},
                    "origin_submission_id": origin_submission_id}
        if result["result"] != Result.waiting:
            result["origin_submission_id"] = origin_submission_id
            return result
        retries -= 1
    return {"result": Result.system_error, "cpu_time": None, "memory": None, "info": {"error": "Too many retires"},
            "origin_submission_id": origin_submission_id}


def release_robot_user(robot_user):
    robot_user.status = RobotUserStatus.free
    robot_user.save(update_fields=["status"])


# local task
@celery_app.task
def submit_waiting_submission(submit_result, problem, robot, robot_user):
    waiting_queue = SubmissionWaitingQueue.objects.all().order_by("create_time")
    if waiting_queue.exists():
        queue_head = waiting_queue.first()
        submission = queue_head.submission
        task_id = submit_dispatcher.delay(problem, submission, robot_user, robot).id
        submission.task_id = task_id
        submission.save(update_fields=["task_id"])
        queue_head.delete()
    else:
        release_robot_user(robot_user)


# local task
@celery_app.task
def update_submission(submit_result, submission):
    submission.origin_submission_id = submit_result["origin_submission_id"]
    submission.result = submit_result["result"]
    submission.cpu_time = submit_result["cpu_time"]
    submission.memory = submit_result["memory"]
    submission.info = json.dumps(submit_result["info"])
    submission.status = SubmissionStatus.done
    submission.save(update_fields=["origin_submission_id", "result", "cpu_time", "memory", "info", "status"])


# local task
@celery_app.task
def submit_dispatcher(problem, submission, robot_user, robot):
    task_id = submit.apply_async(args=(robot, robot_user, problem.submit_url, problem.origin_id,
                                       submission.language, submission.code),
                                 # link相当于执行成功后的回调函数
                                 link=[submit_waiting_submission.s(problem, robot, robot_user),
                                       update_submission.s(submission)]).id
    submission.robot_user = robot_user
    submission.submit_task_id = task_id
    submission.save(update_fields=["submit_task_id", "robot_user"])
