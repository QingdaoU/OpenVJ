# coding=utf-8
from __future__ import unicode_literals

from django.db import models


class OJ(models.Model):
    name = models.CharField(max_length=30)
    is_valid = models.BooleanField(default=True)

    class Meta:
        db_table = "oj"


class APIKey(models.Model):
    api_key = models.CharField(max_length=40)
    name = models.CharField(max_length=40)
    is_valid = models.BooleanField(default=True)
    create_time= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_key"


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


class RobotStatusInfo(models.Model):
    status_info = models.TextField()
    robot_user = models.ForeignKey(RobotUser)
    last_update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "robot_status_info"


class ProblemStatus(models.Model):
    done = 0
    crawling = 1
    failed = 2


class Problem(models.Model):
    oj = models.ForeignKey(OJ)
    url = models.URLField()
    submit_url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    time_limit = models.IntegerField()
    memory_limit = models.IntegerField()
    input_description = models.TextField()
    output_description = models.TextField()
    samples = models.TextField()
    spj = models.BooleanField()
    hint = models.TextField()
    is_valid = models.BooleanField(default=True)
    status = models.IntegerField(choices=((ProblemStatus.done, "Done"),
                                          (ProblemStatus.crawling, "Crawling"),
                                          (ProblemStatus.failed, "Failed")))
    task_id = models.CharField(max_length=40)

    class Meta:
        db_table = "problem"


class Submission(models.Model):
    problem = models.ForeignKey(Problem)
    result = models.IntegerField()
    cpu_time = models.IntegerField()
    memory = models.IntegerField()
    info = models.TextField()
    robot_user = models.ForeignKey(RobotUser)

    class Meta:
        db_table = "submission"
