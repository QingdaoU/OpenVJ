# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from robots.utils import Language, Result


class OJ(models.Model):
    name = models.CharField(max_length=30)
    robot = models.CharField(max_length=50)
    is_valid = models.BooleanField(default=True)

    class Meta:
        db_table = "oj"

    def __str__(self):
        return self.name


class APIKey(models.Model):
    api_key = models.CharField(max_length=40)
    name = models.CharField(max_length=40)
    is_valid = models.BooleanField(default=True)
    create_time= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_key"

    def __str__(self):
        return self.name


class RobotUserStatus(object):
    occupied = 1
    free = 0


class RobotUser(models.Model):
    oj = models.ForeignKey(OJ)
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
    is_valid = models.BooleanField(default=True)
    last_login_time = models.DateTimeField()
    status = models.IntegerField(choices=((RobotUserStatus.occupied, "Occupied"), (RobotUserStatus.free, "Free")))

    class Meta:
        db_table = "robot_user"
        unique_together = (("oj", "username"), )

    def __str__(self):
        return self.oj.name + " - " + self.username


class RobotStatusInfo(models.Model):
    status_info = models.TextField()
    robot_user = models.ForeignKey(RobotUser)
    last_update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "robot_status_info"

    def __str__(self):
        return self.robot_user.username


class ProblemStatus(models.Model):
    done = 0
    crawling = 1
    failed = 2


class Problem(models.Model):
    oj = models.ForeignKey(OJ)
    url = models.URLField()
    origin_id = models.CharField(max_length=30, blank=True, null=True)
    submit_url = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    time_limit = models.IntegerField(blank=True, null=True)
    memory_limit = models.IntegerField(blank=True, null=True)
    input_description = models.TextField(blank=True, null=True)
    output_description = models.TextField(blank=True, null=True)
    samples = models.TextField(blank=True, null=True)
    spj = models.BooleanField(default=False)
    hint = models.TextField(blank=True, null=True)
    is_valid = models.BooleanField(default=True)
    status = models.IntegerField(choices=((ProblemStatus.done, "Done"),
                                          (ProblemStatus.crawling, "Crawling"),
                                          (ProblemStatus.failed, "Failed")))
    task_id = models.CharField(max_length=40)
    create_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "problem"

    def __str__(self):
        if not self.title:
            return self.oj.name + " Problem Status: " + str(self.status)
        else:
            return self.oj.name + " - " + self.title


class SubmissionStatus(object):
    done = 1
    crawling = 2
    failed = 3


class Submission(models.Model):
    api_key = models.ForeignKey(APIKey)
    problem = models.ForeignKey(Problem)
    robot_user = models.ForeignKey(RobotUser)
    language = models.IntegerField(choices=((Language.C, "C", ), (Language.CPP, "CPP"), (Language.Java, "Java")))
    result = models.IntegerField(choices=((Result.accepted, "accepted"),
                                          (Result.wrong_answer, "wrong_answer"),
                                          (Result.compile_error, "compiler_error"),
                                          (Result.format_error, "format_error"),
                                          (Result.memory_limit_exceeded, "memory_limit_exceeded"),
                                          (Result.time_limit_exceeded, "time_limit_exceeded"),
                                          (Result.runtime_error, "runtime_error"),
                                          (Result.system_error, "system_error"),
                                          (Result.waiting, "waiting")))
    cpu_time = models.IntegerField()
    memory = models.IntegerField()
    info = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=((SubmissionStatus.done, "done"),
                                          (SubmissionStatus, "crawling"),
                                          (SubmissionStatus.failed, "failed")))

    class Meta:
        db_table = "submission"

