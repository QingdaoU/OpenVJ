# coding=utf-8
from django.contrib import admin
from .models import OJ, RobotUser, RobotStatusInfo, Problem, Submission

admin.site.register(OJ)
admin.site.register(RobotUser)
admin.site.register(RobotStatusInfo)
admin.site.register(Problem)
admin.site.register(Submission)
