# coding=utf-8
import json
import logging
import traceback
from bottle import route, get, post, run, response, request, Bottle, install

from openvj.settings import INSTALLED_ROBOTS, LOG_LEVEL
from .db import DBHandler, ObjectDoesNotExist


logging.basicConfig(filename='server.log', level=LOG_LEVEL,
                    format="%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] "
                           "[%(module)s:%(funcName)s] [%(levelname)s]- %(message)s")


app = Bottle()


def content_type_plugin(callback):
    def wrapper(*args, **kwargs):
        body = callback(*args, **kwargs)
        response.content_type = "application/json; charset=utf-8"
        return body
    return wrapper


def apikey_auth_plugin(callback):
    def wrapper(*args, **kwargs):
        '''
        api_key = request.headers.get("VJ_API_KEY")
        if not api_key:
            return error("Invalid VJ_API_KEY")
        with DBHandler() as db:
            try:
                db.get("SELECT apikey FROM apikey WHERE apikey = %s and is_valid = 1", (api_key, ))
            except ObjectDoesNotExist:
                return error("VJ_API_KEY does not exist")
        '''
        request.api_key = "123456"
        return callback(*args, **kwargs)
    return wrapper


def server_log_plugin(callback):
    def wrapper(*args, **kwargs):
        try:
            return callback(*args, **kwargs)
        except Exception:
            logging.error(traceback.format_exc())
            return error("Server error")
    return wrapper


def error(reason):
    return json.dumps({"code": 1, "data": reason})


def success(data):
    return json.dumps({"code": 0, "data": data})


def parameter_error(message="参数错误"):
    return error(message)


@route("/")
def index():
    return success("It works")


def import_class(cl):
    d = cl.rfind(".")
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [classname])
    return getattr(m, classname)


@get("/problem/")
def get_problem():
    oj = request.GET.get("oj")
    url = request.GET.get("url")
    if not (oj and url):
        return parameter_error()
    if oj not in INSTALLED_ROBOTS:
        return error("oj不存在")
    Robot = import_class(INSTALLED_ROBOTS[oj]["robot"])
    with DBHandler() as db:
        robot_info = db.first("select robot_status.info "
                               "from robot_status, oj "
                               "where oj.name = %s and robot_status.oj_id = oj.id", (oj, ))
        robot = Robot(**json.loads(robot_info["info"]))
        if not robot.check_url(url):
            return error("url格式错误")
        problem = robot.get_problem(url)
    return success(problem)


install(content_type_plugin)
install(apikey_auth_plugin)
install(server_log_plugin)
run(host='127.0.0.1', port=8081, server='gunicorn', workers=4, debug=True)