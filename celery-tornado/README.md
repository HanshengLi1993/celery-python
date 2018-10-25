# 			Tornado实现异步非阻塞

## 背景简介

Tornado在设计之初就考虑到了性能因素，旨在解决C10K问题，这样的设计使得其成为一个拥有非常高性能的框架。但实际上不是随意用Tornado写一个Web Server都能是高并发的。问题主要还是处在异步非阻塞上，在Web Server中有一些耗时的进程，如查询数据库，意味着应用程序被有效的锁定直至处理结束。这样Tornado的异步非阻塞变成了异步阻塞，极大的影响了性能。

解决方案将耗时的操作，不能异步的操作丢给到RabbitMQ的任务队列中，让celery从任务队列中取任务执行，从而不阻塞Web Server。



## 架构设计

tornado接到请求后，可以把所有的复杂业务逻辑处理、数据库操作以及IO等各种耗时的同步任务交给celery，celery将任务存入RabbitMQ的任务队列中，然后使用worker异步处理完后，再返回给tornado。由此可以看出tornado和celery的交互是异步的，那么整个服务是完全异步的。再加上在tornado中使用异步装饰器，即可实现Web Server的异步非阻塞。

![](C:\Users\F1333239\Desktop\2018-10-22\celery-python\celery-tornado\images\539914515-5b47570ad5364_articlex.png)



## 环境配置

|     MODULE     |   VRESION    |
| :------------: | :----------: |
|    tornado     |    5.1.1     |
| tornado-celery |    0.3.5     |
|      amqp      |    1.4.9     |
|    amqplib     |    1.0.2     |
|      pika      |    0.12.0    |
|     celery     | 3.1.26.post2 |

注意核心模块tornado-celery已经很久没有更新，不能支持celery版本大于4.0



## 异步非阻塞的实现

直接采用tornado-celery在guthub上给的examples来测试

Web Server配置

```python
# tornado_async.py
# # -*- coding:utf-8 -*-

from tornado import gen
from tornado import ioloop
from tornado.web import asynchronous, RequestHandler, Application

import tasks

import tcelery

tcelery.setup_nonblocking_producer()


class AsyncHandler(RequestHandler):
    @asynchronous
    def get(self):
        tasks.sleep.apply_async(args=[3], callback=self.on_result)

    def on_result(self, response):
        self.write(str(response.result))
        self.finish()


class GenAsyncHandler(RequestHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        response = yield gen.Task(tasks.sleep.apply_async, args=[3])
        self.write(str(response.result))
        self.finish()


class GenMultipleAsyncHandler(RequestHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        r1, r2 = yield [gen.Task(tasks.sleep.apply_async, args=[2]),
                        gen.Task(tasks.add.apply_async, args=[1, 2])]
        self.write(str(r1.result))
        self.write(str(r2.result))
        self.finish()


application = Application([
    (r"/async-sleep", AsyncHandler),
    (r"/gen-async-sleep", GenAsyncHandler),
    (r"/gen-async-sleep-add", GenMultipleAsyncHandler),
])

if __name__ == "__main__":
    application.listen(8887)
    ioloop.IOLoop.instance().start()
```

task配置

```python
# tasks.py
# # -*- coding:utf-8 -*-

import os
import time
from datetime import datetime
from celery import Celery

celery = Celery("tasks", broker="amqp://user:password@host:port//")
celery.conf.CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'amqp')


@celery.task
def add(x, y):
    return int(x) + int(y)


@celery.task
def sleep(seconds):
    time.sleep(float(seconds))
    return seconds


@celery.task
def echo(msg, timestamp=False):
    return "%s: %s" % (datetime.now(), msg) if timestamp else msg


@celery.task
def error(msg):
    raise Exception(msg)


if __name__ == "__main__":
    celery.start()
```

运行

```shell
# --app的参数为tasks.py文件相对路径
$ python -m tcelery --port=8888 --app=tasks --address=0.0.0.0
```

测试

```shell
$ curl -X POST -d '{"args":["hello"]}' http://localhost:8888/apply-async/examples.tasks.echo/
{"task-id": "a24c9e38-4976-426a-83d6-6b10b4de7ab1", "state": "PENDING"}
```



## 深入学习

#### 队列过长问题

使用上述方案，会将请求任务数据存储在RabbitMQ的了队列中。若队列中的任务过多，则可能导致长时间等待，降低效率；部分请求任务无法进入任务队列导致请求失效。

解决方案：

- 建立多个任务queue，把大量的任务分发到不同的queue中，减轻单个queue时可能出现的任务数量过载。具体参数设置参考([Message Routing](http://docs.jinkan.org/docs/celery/configuration.html#id18))[http://docs.jinkan.org/docs/celery/configuration.html#message-routing]
- 搭建高可用的RabbitMQ集群，将celery的worker与tornado的Web Server分离。使用分布式celery执行任务，增加队列消息消费速度。若本项目部署在K8S环境中可通过监控任务队列数量来实现worker的HPA。
- 启动多个celery worker监听任务队列，使用多进程并发消费任务队列，celery命令可以通过-concurrency参数来指定用来执行任务而prefork的worker进程，如果所有的worker都在执行任务，那么新添加的任务必须要等待有一个正在执行的任务完成后才能被执行，默认的concurrency数量是机器上CPU的数量。另外，celery是支持好几个并发模式的，有prefork，threading，协程（gevent，eventlet），prefork在celery的介绍是，默认是用了multiprocess来实现的；可以通过-p参数指定其他的并发模型，如gevent（需自己配置好gevent环境）。

## 参考文档

[tornado配合celery及rabbitmq实现web request异步非阻塞](https://segmentfault.com/a/1190000015619549)

[使用tornado让你的请求异步非阻塞](https://blog.csdn.net/chenyulancn/article/details/45888949?utm_source=blogxgwz0)

[tornado 简易教程](https://blog.csdn.net/belalds/article/details/80575755)