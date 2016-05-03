# coding=utf-8
import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': "vj",
        'CONN_MAX_AGE': 0.1,
        'HOST': os.environ["MYSQL_PORT_3306_TCP_ADDR"],
        'PORT': 3306,
        'USER': os.environ["MYSQL_ENV_MYSQL_USER"],
        'PASSWORD': os.environ["MYSQL_ENV_MYSQL_ROOT_PASSWORD"]
    }
}

REDIS_LOCAL_QUEUE = {
    "host": os.environ["REDIS_PORT_6379_TCP_ADDR"],
    "port": 6379,
    "db": 3,
    "password": ":" + os.environ["REDIS_PASSWORD"] + "@"
}
