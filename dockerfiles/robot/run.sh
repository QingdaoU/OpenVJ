#!/usr/bin/env bash
celery -A robot.tasks worker -l DEBUG