FROM python:3.5
ENV PYTHONBUFFERED 1
RUN mkdir -p /code /code/log
COPY requirements.txt /tmp
RUN pip install -i http://pypi.douban.com/simple  -r /tmp/requirements.txt --trusted-host pypi.douban.com
WORKDIR /code
CMD bash /code/dockerfiles/robot/run.sh