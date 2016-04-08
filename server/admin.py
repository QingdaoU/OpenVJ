# coding=utf-8
from django.contrib import admin
from .models import OJ, RobotUser, RobotStatusInfo, Problem, Submission, APIKey, SubmissionWaitingQueue


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "create_time"]

admin.site.register(APIKey, APIKeyAdmin)


class OJAdmin(admin.ModelAdmin):
    list_display = ["name", "robot", "is_valid"]

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(OJ, OJAdmin)


class RobotUserAdmin(admin.ModelAdmin):
    list_display = ["oj", "username", "last_login_time", "status", "is_valid"]

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

admin.site.register(Submission, SubmissionAdmin)


admin.site.register(SubmissionWaitingQueue)