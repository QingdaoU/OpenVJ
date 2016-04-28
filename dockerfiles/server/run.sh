#!/usr/bin/env bash

gunicorn openvj.wsgi:application -b 0.0.0.0:8080 --user nobody --group nogroup --reload &
wait