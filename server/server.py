# coding=utf-8
import json
from bottle import route, run
from .db import DBHandler


@route("/")
def index():
    with DBHandler() as db:
        r = db.filter("select * from apikey where name = %s", ("test", ))
        return r

run(host='127.0.0.1', port=8081, server='gunicorn', workers=4)