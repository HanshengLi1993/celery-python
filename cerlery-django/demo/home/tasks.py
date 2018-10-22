from __future__ import absolute_import

from celery import task

from celery import shared_task


# from celery.task import tasks
# from celery.task import Task

@task()
# @shared_task
def add(x, y):
    print("%d + %d = %d" % (x, y, x + y))
    return x + y


# class AddClass(Task):
#    def run(x,y):
#        print "%d + %d = %d"%(x,y,x+y)
#        return x+y
# tasks.register(AddClass)

@shared_task
def mul(x, y):
    print("%d * %d = %d" % (x, y, x * y))
    return x * y


@shared_task
def sub(x, y):
    print("%d - %d = %d" % (x, y, x - y))
    return x - y
