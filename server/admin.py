# coding=utf-8
import json
from django.contrib import admin
from .utils import import_class
from .models import OJ, RobotUser, RobotStatusInfo, Problem, Submission, APIKey, SubmissionWaitingQueue


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "create_time"]

admin.site.register(APIKey, APIKeyAdmin)


class OJAdmin(admin.ModelAdmin):
    list_display = ["name", "robot", "is_valid"]

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(OJ, OJAdmin)


def login_user_action(modeladmin, request, queryset):
    for user in queryset.filter(is_valid=True):
        robot = import_class(user.oj.robot)()
        robot.login(user.username, user.password)
        info = robot.save()
        try:
            status_info = RobotStatusInfo.objects.get(robot_user=user)
            status_info.status_info = json.dumps(info)
            status_info.save()
        except RobotStatusInfo.DoesNotExist:
            RobotStatusInfo.objects.create(status_info=json.dumps(info), robot_user=user)


login_user_action.short_description = "login user"


class RobotUserAdmin(admin.ModelAdmin):
    list_display = ["oj", "username", "last_login_time", "status", "is_valid"]
    actions = [login_user_action]

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(RobotUser, RobotUserAdmin)


class RobotStatusInfoAdmin(admin.ModelAdmin):
    list_display = ["robot_user", "last_update_time"]

admin.site.register(RobotStatusInfo, RobotStatusInfoAdmin)


class ProblemAdmin(admin.ModelAdmin):
    list_display = ["oj", "title", "create_time", "status", "is_valid"]
    search_fields = ["title", "description"]

admin.site.register(Problem, ProblemAdmin)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["api_key", "problem", "language", "result", "create_time", "status"]
    ordering = ["create_time"]

admin.site.register(Submission, SubmissionAdmin)


admin.site.register(SubmissionWaitingQueue)