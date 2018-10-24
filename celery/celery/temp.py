# tasks.py
# -*-coding:utf-8 -*-

from celery import Celery, chain

app = Celery('tasks',
             backend='redis://user:password@host:port/db',
             broker='redis://user:password@host:port/db')


def calculate():
    # res_add = add.delay(1, 2).get()
    # res_mul = mul.delay(res_add, 3).get()
    # res_sub = sub.delay(res_mul, 4).get()
    # res_sub = add.apply_async((1, 2), link=[mul.s(3), sub.s(4)]).get()
    res_sub = chain(add.s(1, 2), mul.s(3), sub.s(4)).get()
    return res_sub


@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def sub(x, y):
    return x - y
