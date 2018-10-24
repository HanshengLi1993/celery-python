# -*-coding:utf-8 -*-

import time
from celery import Celery,chain
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = Celery()
app.config_from_object('config')


# 装饰器app.task将add(x,y)修饰成celery task对象
@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def sub(x, y):
    return x - y


# @app.task
def calculate():
    # res_add = add.delay(1, 2).get()
    # res_mul = mul.delay(res_add, 3).get()
    # res_sub = sub.delay(res_mul, 4).get()
    # res_sub = add.apply_async((1, 2), link=[mul.s(3), sub.s(4)]).get()
    res_sub = chain(add.s(1, 2), mul.s(3), sub.s(4))().get()
    return res_sub


@app.task(bind=True)
def period_task(self):
    logger.info(self.request.__dict__)
    print('period task done: {0}'.format(self.request.id))


@app.task(bind=True)
def update_progress(self):
    for i in range(0):
        time.sleep(0.1)
        self.update_state(state="PROGRESS", meta={'p': i * 10})
    return 'finish'
