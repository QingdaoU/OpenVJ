# coding=utf-8
from rest_framework.response import Response


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
