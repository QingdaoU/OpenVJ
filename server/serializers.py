# coding=utf-8
import json

from rest_framework import serializers

from robots.utils import Language
from .models import Problem


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