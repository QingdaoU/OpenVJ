# coding=utf-8
import json

from rest_framework import serializers

from robots.utils import Language
from .models import Problem, Submission


class JSONField(serializers.Field):
    def to_representation(self, value):
        return json.loads(value)


class ProblemSerializer(serializers.ModelSerializer):
    samples = JSONField()

    class Meta:
        model = Problem


class CreateSubmissionSerializer(serializers.Serializer):
    problem_id = serializers.CharField(max_length=32)
    language = serializers.ChoiceField(choices=[Language.C, Language.CPP, Language.Java])
    code = serializers.CharField(max_length=10000)


class SubmissionSerializer(serializers.ModelSerializer):
    info = JSONField()

    class Meta:
        model = Submission
        exclude = ["submit_task_id", "task_id", "robot_user", "origin_submission_id", "api_key"]