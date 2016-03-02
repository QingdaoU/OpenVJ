# coding=utf-8
class Language(object):
    C = 0
    CPP = 1
    Java = 2


class Result(object):
    accepted = 0,
    runtime_error = 1
    time_limit_exceeded = 2,
    memory_limit_exceeded = 3
    compile_error = 4
    format_error = 5
    wrong_answer = 6
    system_error = 7
    waiting = 8