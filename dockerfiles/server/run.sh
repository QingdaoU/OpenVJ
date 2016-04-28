#!/usr/bin/env bash
if [ ! -f "/code/openvj/custom_settings.py" ]; then
 cp /code/openvj/custom_settings.example.py /code/openvj/custom_settings.py
 echo "SECRET_KEY=\"`cat /dev/urandom | head -1 | md5sum | head -c 32`\"" >> /code/openvj/custom_settings.py
fi
find /code -name "*.pyc" -delete
python -m compileall /code
gunicorn openvj.wsgi:application -b 0.0.0.0:8080 --user nobody --group nogroup --reload &
celery -A openvj worker -l DEBUG -Q local &
wait