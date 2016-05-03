# coding=utf-8
import time
import os

from openvj import celery_app as app
from .utils import Result


# remote robot task
@app.task
def get_problem(robot, url):
    return robot.get_problem(url)


# remote robot task
@app.task
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