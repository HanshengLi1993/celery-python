# 		django-celery动态添加定时任务

## 功能简介

使用celery代替crontab实现实时添加定时任务的效果，并且结合django的后台功能管理这些任务。

![](https://github.com/HanshengLi1993/celery-python/blob/master/cerlery-django/demo/images/main_page.bmp)

## 环境配置

本文基于python3.4.4为语言环境，模块版本列表如下所示：

| MODULE            | VERSION      |
| ----------------- | ------------ |
| celery            | 3.1.26.post2 |
| Django            | 1.9.2        |
| django-celery     | 3.2.2        |
| celery-with-redis | 3.0          |
| flower            | 0.9.2        |

需要注意的是django-celery最新版本是3.2.2，并且没有在继续更新。但celery的某些功能在4.0才可以使用，但django-celery不支持celery4.0版本。

```shell
$ django-celery 3.2.2 has requirement celery<4.0,>=3.1.15, but you'll have celery 4.0.0 which is incompatible.
```

## 创建Django项目

```shell
# 创建项目demo
$ Django-admin startproject demo
$ cd demo
# 创建应用
$ python manage.py startapp home
```

最终得到的目录如下所示：

![](https://github.com/HanshengLi1993/celery-python/blob/master/cerlery-django/demo/images/project_index.bmp)

### 加入celery配置

```python
# ./demo/demo/setting.py
# -*-coding:utf-8 -*-

import djcelery

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'home',  # 导入自定义app模块
    'djcelery',  # 导入django-celery模块
)
# 配置时区，默认的UTC时间会比东八区慢8个小时
TIME_ZONE = 'Asia/Shanghai'
djcelery.setup_loader()  # 导入默认配置
BROKER_URL = 'redis://@127.0.0.1:6379/0' # 配置消息队列
BROKER_TRANSPORT = 'redis' 
CELERY_TIMEZONE = 'Asia/Shanghai' 
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'  # 数据库调度
```

### 创建task

```python
# ./demo/home/tasks.py
# -*-coding:utf-8 -*-

from __future__ import absolute_import
from celery import task,shared_task


@task()
def add(x, y):
    print("%d + %d = %d" % (x, y, x + y))
    return x + y


@shared_task
def mul(x, y):
    print("%d * %d = %d" % (x, y, x * y))
    return x * y


@shared_task
def sub(x, y):
    print("%d - %d = %d" % (x, y, x - y))
    return x - y
```

### 绑定task与设置

```python
# ./demo/demo/celery.py
# -*-coding:utf-8 -*-

from __future__ import absolute_import

import os
from celery import Celery
from django.conf import settings

# 导入setting.py 文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings')

# 新建任务名
app = Celery('demo')

# 导入配置文件
app.config_from_object('django.conf:settings')
# 设置任务自发现的扫描位置
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
```

代码构建已经完成，下面开始系统配置：

```shell
# pwd ./demo
# 为Django后台新增账户
$ python manage.py createsuperuser
# 同步Django数据库
$ python manage.py makemigrations
$ python manage.py migrate
# 启动Django web server
$ python manage.py runserver 0.0.0.0:8001
# 启动 celery beat 监听并自动触发任务队列
$ python manage.py celery beat
# 启动celery worker 正式环境将 -l dubug 改为 -l info
$ python manage.py celery worker -c -6 -l debug
# 启动celery监控web server
$ celery flower --port=8000 --broker=redis://@127.0.0.1:6379/0
```

效果展示

![](https://github.com/HanshengLi1993/celery-python/tree/master/cerlery-django/demo/images/function_display.bmp)

- Crontab:管理任务的执行时间
- Interval：管理任务的执行周期
- Periodic tasks：管理定时任务
- Tasks：管理任务
- Workers：管理执行者

在`Crontab`，`Interval`中设置好时间配置后，进入`Periodic tasks`中添加任务，让其自动执行。

![](https://github.com/HanshengLi1993/celery-python/tree/master/cerlery-django/demo/images/crontabs.bmp)

![](https://github.com/HanshengLi1993/celery-python/blob/master/cerlery-django/demo/images/intervals.bmp)

![](https://github.com/HanshengLi1993/celery-python/blob/master/cerlery-django/demo/images/periodic_tasks.bmp)

![](https://github.com/HanshengLi1993/celery-python/blob/master/cerlery-django/demo/images/periodic_tasks_add.bmp)

- Name: 这一定期任务的注册名
- Task (registered): 可以选择所有已经注册的task之一, 例如前面的add function
- Task (custom): task的全名, 例如myapp.tasks.add, 但最好还是用以上项
- Enabled: 是否开启这一定期任务
- Interval: 定期任务的间隔时间, 例如每隔5分钟
- Crontab: 如果希望task在某一特定时间运行, 则使用Unix中的Crontab代替interval
- Arguments: 用于传参数到task中
- Execution Options: 更高级的设置

![](https://github.com/HanshengLi1993/celery-python/tree/master/cerlery-django/demo/images/flower_dashboard.bmp)

flower的更多用法参考[flower-real-time-celery-web-monitor](http://docs.celeryproject.org/en/latest/userguide/monitoring.html#flower-real-time-celery-web-monitor)

## 更多尝试

task自发现：

在django web server和celery beat、celery worker都启动着的情况下，修改`./demo/home/tasks.py`文件，新增task function 后,在上图`Task (registered)`下拉列表中能实时看到新增的task，验证了Django的`autodiscover_tasks`功能有效。同时，beat的服务扫描可以发现新增的crontab任务，并尝试去自动执行。

![](https://github.com/HanshengLi1993/celery-python/tree/master/cerlery-django/demo/images/beat.bmp)

但在不重启celery worker的情况下，worker无法发现新添加的task任务，导致报错。

![](https://github.com/HanshengLi1993/celery-python/tree/master/cerlery-django/demo/images/error_task.bmp)

在celery4.2版本后加入了`--autoreload`启动参数，在原生的celery中，--autoreload要搭配`CELERY_IMPORT`或`include`设定来用（autoreload这两项设定中的module文件），可以解决worker的任务自发现的问题。但由于`django-celery`模块不再更新，无法支持celery4.2，因此本功能不发实现。

django正式上线后，需要将`settings.py`中的"`DEBUG = True`注释掉免得内存泄漏，同时在下面加上`ALLOWED_HOSTS = ['HOST']`。这时候Django的admin管理页面会无法加载样式文件，因为非debug模式下django server不会帮忙处理静态文件。解决方案是在启动django server的时候添加`--insecure`选项([参考文章](http://stackoverflow.com/questions/5836674/why-does-debug-false-setting-make-my-django-static-files-access-fail ))，使用该选项要确定`settings.py`的`INSTALLED_APPS`中有`django.contrib.staticfiles`。

```shell
# 启动Django web server 关闭DEBUG模式 
$ python manage.py runserver 0.0.0.0:8001 --insecure
```



## 参考文档

[官方文档](http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html)

[django-celery动态添加定时任务](https://blog.csdn.net/Vintage_1/article/details/47664297)
