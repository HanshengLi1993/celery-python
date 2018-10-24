# trigger.py
# -*-coding:utf-8 -*-

import sys
import time
from tasks import update_progress, add, mul,calculate
from celery import  chain


def show_progress(body):
    res = body.get('result')
    if body.get('status') == 'PROGRESS':
        # 在屏幕上实时看到输出信息
        sys.stdout.write('\r任务进度: {0}%'.format(res.get('p')))
        sys.stdout.flush()
    else:
        print('\r' + res)


if __name__ == '__main__':
    # # 算术加法
    # result = add.delay(4, 4)  # 不要直接 add(4, 4)，这里需要用 celery 提供的接口 delay 进行调用
    # while not result.ready():
    #     time.sleep(1)
    # print('task done: {0}'.format(result.get()))
    #
    # 显示任务实时进度

    # result = update_progress.apply_async()
    # print(result.get(setting_on_message=show_progress, propagate=False))
    result = calculate()
    print('task done: {0}'.format(result))

    # result = add.apply_async((1, 2), link=add.s(3))
    # result = chain(add.s(1, 2), mul.s(3))()
    # print('task done: {0}'.format(result.get()))
