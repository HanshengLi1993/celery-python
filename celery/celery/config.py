# config.py
# -*-coding:utf-8 -*-

import celery
from datetime import timedelta
from celery.schedules import crontab

# broker
BROKER_URL = 'redis://@127.0.0.1:6379/0'
# backend
CELERY_RESULT_BACKEND = 'redis://@127.0.0.1:6379/0'
# 导入任务，如tasks.py
CELERY_IMPORTS = ('tasks', )
# 列化任务载荷的默认的序列化方式
CELERY_TASK_SERIALIZER = 'json'
# 结果序列化方式
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
# 时间地区与形式
CELERY_TIMEZONE = 'Asia/Shanghai'
# 时间是否使用utc形式
CELERY_ENABLE_UTC = True

# 设置任务的优先级或任务每分钟最多执行次数
CELERY_ROUTES = {
    # 如果设置了低优先级，则可能很久都没结果
    # 'tasks.add': 'low-priority',
    # 'tasks.add': {'rate_limit': '10/m'}，
    # 'tasks.add': {'rate_limit': '10/s'}，
    # '*': {'rate_limit': '10/s'}
}

# 周期性任务配置
CELERYBEAT_SCHEDULE = {
    # 周期任务
    'add-every-30-seconds': {
        'task': 'tasks.add',
        'schedule': timedelta(seconds=30),
        'args': (16, 16)
    },
    # 定时任务
    # Executes every Monday morning at 7:30 A.M
    'add-every-monday-morning': {
        'task': 'tasks.add',
        'schedule': crontab(hour=7, minute=30, day_of_week=1),
        'args': (16, 16),
    },
}

# borker池，默认是10
BROKER_POOL_LIMIT = 10
# 任务过期时间，单位为s，默认为一天
CELERY_TASK_RESULT_EXPIRES = 3600
# backend缓存结果的数目，默认5000
CELERY_MAX_CACHED_RESULTS = 10000


# BROKER_USE_SSL 使用证书连接broker，对redis，rabbitmq有支持
class MyTask(celery.Task):
    def on_success(self, retval, task_id, args, kwargs):
        print('task done: {0}'.format(retval))
        return super(MyTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('task fail, reason: {0}'.format(exc))
        return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)


# 针对任务add，当发生执行成功或失败的时候所执行的操作
CELERY_ANNOTATIONS = {'tasks.add':
                          {'on_failure': MyTask().on_failure,
                           'on_success': MyTask().on_success}
                      }

SPIDER_URL = "https://www.taobao.com"
MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
MONGO_TABLE = 'product'
SERVICE_ARGS = ['--load-images=false', '--disk-cache=true']
KEY_WORD = "美食"
