# coding=utf-8
from rest_framework import serializers

from robots.utils import Language
from .models import Problem


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem


class CreateSubmissionSerializer(serializers.Serializer):
    url = serializers.URLField()
    language = serializers.ChoiceField(choices=[Language.C, Language.CPP, Language.Java])
    code = serializers.CharField(max_length=10000)