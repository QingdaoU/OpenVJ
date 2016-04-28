# coding=utf-8
import time
import os

from celery import Celery
from .utils import Result

if os.environ.get("robot_env", "local") == "local":
    REDIS_ROBOT_QUEUE = {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 3
    }
else:
    REDIS_ROBOT_QUEUE = {
        "host": os.environ["REDIS_PORT_6379_TCP_ADDR"],
        "port": 6379,
        "db": 3,
        "password": os.environ["REDIS_PASSWORD"]
    }


def _redis_password():
    password = REDIS_ROBOT_QUEUE.get("password")
    if password:
        return password + "@"
    else:
        return ""


app = Celery('tasks', broker="redis://{password}{host}:{port}/{db}".format(password=_redis_password(),
                                                                           host=REDIS_ROBOT_QUEUE["host"],
                                                                           port=REDIS_ROBOT_QUEUE["port"],
                                                                           db=REDIS_ROBOT_QUEUE["db"]))


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