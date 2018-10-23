FROM python:3-slim

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

RUN mkdir /demo
RUN mkdir /var/log/celery-django

WORKDIR /demo
CMD python manage.py runserver 0.0.0.0:8001
CMD python manage.py celery beat
CMD python manage.py  celery worker -c 6 -l info