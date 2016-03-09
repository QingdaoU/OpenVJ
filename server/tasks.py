# coding=utf-8
from __future__ import absolute_import
from celery import shared_task


@shared_task
def get_problem(robot, url):
    return robot.get_problem(url)