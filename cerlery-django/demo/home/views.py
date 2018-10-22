# coding:utf-8
from django.shortcuts import render, render_to_response
from django.http import HttpResponse

from .tasks import mul, add


def index(request):
    # mul.delay()
    # sendEmail.delay()
    # return HttpResponse(u"欢迎光临 自强学堂!")
    return render_to_response('index.html', locals())


def success(request):
    add.delay()
    return HttpResponse()
    # return render_to_response('success.html', locals())
