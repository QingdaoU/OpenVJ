# coding=utf-8
import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


REDIS = {
    "HOST": "127.0.0.1",
    "PORT": 6379,
    "PASSWORD": "123456"
}


# celery配置
BROKER_URL = "redis://{host}:{port}/{db}".format(host=REDIS["HOST"], port=REDIS["PORT"], db=0)
CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = REDIS["HOST"]
CELERY_REDIS_PORT = REDIS["PORT"]
CELERY_REDIS_DB = 0