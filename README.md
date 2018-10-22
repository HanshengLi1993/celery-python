# 			分布式任务队列Celery

Celery （芹菜）是基于Python开发的分布式任务队列。它支持使用任务队列的方式在分布的机器／进程／线程上执行任务调度。



## 架构设计

![](https://github.com/HanshengLi1993/celery-python/images/539914515-5b47570ad5364_articlex.png)

### 核心部件

- broker

  Celery 扮演生产者和消费者的角色，brokers 就是生产者和消费者存放/拿取产品的地方(任务队列)

  - 消息队列，由第三方消息中间件完成
  - 常见有RabbitMQ, Redis, MongoDB等

- worker

  Celery 中的工作者，类似与生产/消费模型中的消费者，其从队列中取出任务并执行

  - 任务执行器
  - 可以有多个worker进程
  - worker又可以起多个queue来并行消费消息

- backend

  队列中的任务运行完后的结果或者状态需要被任务发送者知道，那么就需要一个地方储存这些结果，就是 backend

  - 后端存储，用于持久化任务执行结果

### 功能部件

- beat
  - 定时器，用于周期性调起任务
- flower
  - web管理界面



## 快速入门

### 定义任务

Celery 的第一个参数是当前模块的名称，这个参数是必须的，这样的话名称可以自动生成。第二个参数是消息中间件关键字参数，指定你所使用的消息中间件的 URL，此处使用了 redis。

```python
# tasks.py
# -*-coding:utf-8 -*-

from celery import Celery

# 任务名称
# backend 用于存储结果
# broker 用于存储消息队列
app = Celery('mytasks',
             backend='redis://user:password@host:port/db',
             broker='redis://user:password@host:port/db')

# 装饰器app.task将add(x,y)修饰成celery task对象
@app.task
def add(x, y):
    return x + y
```

Celery支持稳定的消息中间件有Redis('redis://')和RabbitMQ(amqp://)。

### 启动服务

步骤：

- 启动任务工作者(worker)
- 将任务放入消息队列
- worker读取消息队列，并执行任务

```shell
# -A 指定celery名称，loglevel制定log级别，只有大于或等于该级别才会输出到日志文件
$ celery -A mytasks worker --loglevel=info
```

启动一个工作者监听mytasks任务集合，同时创建一个任务队列mytasks（当然此时broker中还没有任务，worker此时相当于待命状态）

### 触发任务

现在我们已经有一个celery队列了，我门只需要将工作所需的参数放入队列即可

```python
# celery.py
# -*-coding:utf-8 -*-

from tasks import add

result = add.delay(4, 4) #不要直接 add(4, 4)，这里需要用 celery 提供的接口 delay 进行调用
while not result.ready():
    time.sleep(1)
print（'task done: {0}'.format(result.get())）
```

调用任务会返回一个 AsyncResult 实例，可用于检查任务的状态，等待任务完成或获取返回值（如果任务失败，则为异常和回溯）。但这个功能默认是不开启的，你需要设置一个 Celery 的结果后端(即backen，我们在tasks.py中已经设置了，backen就是用来存储我们的计算结果)。

常用接口

- tasks.add(4,6) ---> 本地执行
- tasks.add.delay(3,4) --> worker执行
- t=tasks.add.delay(3,4) --> t.get() 获取结果，或卡住，阻塞
- t.ready()---> False：未执行完，True：已执行完
- t.get(propagate=False) 抛出简单异常，但程序不会停止
- t.traceback 追踪完整异常



## 进阶用法

## 使用配置

- 使用配置来运行，对于正式项目来说可维护性更好。配置可以使用app.config.XXXXX_XXX='XXX'的形式如app.conf.CELERY_TASK_SERIALIZER = 'json'来进行配置
- [配置资料](http://docs.jinkan.org/docs/celery/configuration.html#broker-settings)

### 配置文件

```python
# config.py
# -*-coding:utf-8 -*-
from datetime import timedelta
from celery.schedules import crontab

# broker
BROKER_URL = 'redis://:password@host:port/db'
# backend
CELERY_RESULT_BACKEND = 'redis://:password@host:port/db'
# 导入任务，如tasks.py
CELERY_IMPORTS = ('tasks', )
# 列化任务载荷的默认的序列化方式
CELERY_TASK_SERIALIZER = 'json'
# 结果序列化方式
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
# 时间地区与形式
CELERY_TIMEZONE = 'Europe/Oslo'
# 时间是否使用utc形式
CELERY_ENABLE_UTC = True

# 设置任务的优先级或任务每分钟最多执行次数
CELERY_ROUTES = {
    # 如果设置了低优先级，则可能很久都没结果
    #'tasks.add': 'low-priority',
    #'tasks.add': {'rate_limit': '10/m'}，
    #'tasks.add': {'rate_limit': '10/s'}，
    #'*': {'rate_limit': '10/s'}
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
```

### 分布式

- 启动多个celery worker，这样即使一个worker挂掉了其他worker也能继续提供服务

  - 方法一

  ```shell
  # 启动三个worker：w1,w2,w3
  $ celery multi start w1 -A mytasks -l info
  $ celery multi start w2 -A mytasks -l info
  $ celery multi start w3 -A mytasks -l info
  # 立即停止w1,w2，即便现在有正在处理的任务
  $ celery multi stop w1 w2
  # 重启w1
  $ celery multi restart w1 -A mytasks -l info
  # 待任务执行完，停止
  $ celery multi stopwait w1 w2 w3    
  ```

  - 方法二

  ```shell
  # 启动多个worker，但是不指定worker名字
  # 你可以在同一台机器上运行多个worker，但要为每个worker指定一个节点名字，使用--hostname或-n选项
  # concurrency指定处理进程数，默认与cpu数量相同，因此一般无需指定
  $ celery -A mytasks worker --loglevel=INFO --concurrency=10 -n worker1@%h
  $ celery -A mytasks worker --loglevel=INFO --concurrency=10 -n worker2@%h
  $ celery -A mytasks worker --loglevel=INFO --concurrency=10 -n worker3@%h
  ```

### 根据任务状态执行不同操作

- 通过装饰器属性实现

  任务执行后，根据任务状态执行不同操作需要我们复写 task 的 `on_failure`、`on_success`等方法：

```python
# tasks.py
# -*-coding:utf-8 -*-

class MyTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print 'task done: {0}'.format(retval)
        return super(MyTask, self).on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print 'task fail, reason: {0}'.format(exc)
        return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)

@app.task(base=MyTask)
def add(x, y):
    return x + y
```

​	给修饰器`app.task`加上base参数来决定修饰后的 task 对象的base属性，通过判断任务add执行是否完成，	调用`on_failure`、`on_success`方法。

- 通过配置文件实现

  在配置文件中指定CELERY_ANNOTATIONS属性的值。

```python
# config.py
# -*-coding:utf-8 -*-

def on_success(self, retval, task_id, args, kwargs):
    print 'task done: {0}'.format(retval)
    return super(MyTask, self).on_success(retval, task_id, args, kwargs)
    
def on_failure(self, exc, task_id, args, kwargs, einfo):
    print 'task fail, reason: {0}'.format(exc)
    return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)

# 针对任务add，当发生执行成功或失败的时候所执行的操作
CELERY_ANNOTATIONS = {'tasks.add': 
                      {'on_failure': my_on_failure,
                       'on_success':my_on_failure}
                     }   
```

### 绑定任务为实例方法

```python
# tasks.py
# -*-coding:utf-8 -*-

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@app.task(bind=True)
def add(self, x, y):
    logger.info(self.request.__dict__)
    return x + y
```

让被修饰的函数add成为 task 对象的绑定方法，这样就相当于被修饰的函数 add 成了 task 的实例方法，可以调用 self 获取当前 task 实例的很多状态及属性。

request属性文档：[celery.task.request](http://docs.celeryproject.org/en/latest/userguide/tasks.html#task-request-info)

### 任务状态回调

在实际应用场景中得知实时任务状态是很常见的需求。Celery的默认任务状态如下所示：

|  参数   |     说明     |
| :-----: | :----------: |
| PENDING |  任务等待中  |
| STARTED |  任务已开始  |
| SUCCESS | 任务执行成功 |
| FAILURE | 任务执行失败 |
|  RETRY  | 任务将被重试 |
| REVOKED |   任务取消   |

实现实时追踪摸个任务的执行进度，可以通过自定义一个任务状态并通过回调将任务进度返回。

```python
# tasks.py
# -*-coding:utf-8 -*-

import time
from celery import Celery

@app.task(bind=True)
def update_progress(self):
    for i in range(0):
        time.sleep(0.1)
        self.update_state(state="PROGRESS", meta={'p': i*10})
    return 'finish'
```

sadasdasd

```python
# celery.py
# -*-coding:utf-8 -*-

import sys
from task import update_progress

def show_progress(body):
    result = body.get('result')
    if body.get('status') == 'PROGRESS':
        # 在屏幕上实时看到输出信息
        sys.stdout.write('\r任务进度: {0}%'.format(res.get('p')))
        sys.stdout.flush()
    else:
        print('\r' + result)
        
if __name__ == '__main__':
	result = show_progress.delay()
	print result.get(on_message=show_progress, propagate=False)
```

```python
# config.py
# -*-coding:utf-8 -*-

# 中国使用上海时区
CELERY_TIMEZONE = 'Asia/Shanghai'
```

### 定时/周期任务

可以通过定义配置文件中可以看到CELERYBEAT_SCHEDULE键值来新建定时任务或周期任务。

`schedule`：任务执行的时间安排。周期执行选择datetime.timedelta；定期执行选择crontab。具体周期配置参考[crontab-schedules](http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#crontab-schedules)

定时任务需要用到datetime模块时，需要校准时区，默认UTC。

然后将配置好的配置文件绑定到任务上：

```python
# tasks.py
# -*-coding:utf-8 -*-

from config.py import *

app = Celery('mytasks', 
             backend='redis://:password@host:port/db',
             broker='redis://:password@host:port/db')
app.config_from_object('config')

@app.task(bind=True)
def period_task(self):
    print('period task done: {0}'.format(self.request.id))
```

最后启动worker，并运行 beat，监听并自动触发定时/周期性任务：

```shell
$ celery -A mytasks worker --loglevel=info
# 每十秒扫瞄一次任务，检查知否有新任务加入。beat会触发定时/周期性任务在改后台自动执行
$ celery -A mytasks beat -l debug --max-interval=10 
```

### 链式任务

### 调用任务

### 关于 AsyncResult

## 参考文档

- [中文文档](http://docs.jinkan.org/docs/celery/getting-started/first-steps-with-celery.html)

- [官方文档](http://docs.celeryproject.org/en/latest/userguide/workers.html)

- [Celery任务队列](https://segmentfault.com/a/1190000013424206)

- [分布式队列神器 Celery](https://segmentfault.com/a/1190000008022050)
