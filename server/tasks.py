# coding=utf-8
from __future__ import absolute_import
import time
import json

from openvj import celery_app
from robots.tasks import submit, get_problem
from .models import RobotUserStatus, SubmissionStatus, SubmissionWaitingQueue


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
