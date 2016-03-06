# coding=utf-8
import json
from bottle import route, run, response, request, Bottle, install
from .db import DBHandler, ObjectDoesNotExist

app = Bottle()
app.config["autojson"] = True


def content_type_plugin(callback):
    def wrapper(*args, **kwargs):
        body = callback(*args, **kwargs)
        response.content_type = "application/json; charset=utf-8"
        return body
    return wrapper


def apikey_auth_plugin(callback):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("VJ_API_KEY")
        if not api_key:
            return error("Invalid VJ_API_KEY")
        with DBHandler() as db:
            try:
                db.get("SELECT id FROM apikey WHERE apikey = %s", (api_key, ))
            except ObjectDoesNotExist:
                return error("VJ_API_KEY does not exist")
        return callback(*args, **kwargs)
    return wrapper


def error(reason):
    return json.dumps({"code": 1, "data": reason})


def success(data):
    return json.dumps({"code": 0, "data": data})


@route("/")
def index():
    return success(request.headers["VJ_API_KEY"])
    '''
    with DBHandler() as db:
        r = db.filter("select * from apikey where name = %s", ("test", ))
        for item in r:
            item["create_time"] = item["create_time"].strftime("%Y-%-m-%-d %X")
        return "123"
    '''

install(content_type_plugin)
install(apikey_auth_plugin)
run(host='127.0.0.1', port=8081, server='gunicorn', workers=4, debug=True)