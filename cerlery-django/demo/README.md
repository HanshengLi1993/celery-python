# 		django-celery动态添加定时任务




celery -A demo worker -l debug

celery -A demo beat -l debug --max-interval=10 # 每十秒扫瞄任务

python3 manage.py createsuperuser

python3 manage.py runserver

127.0.0.1:8000/admin/

python3 manage.py runserver 0.0.0.0:8001#启动django的应用，可以动态的使用django-admin来管理任务

python3 manage.py celery beat #应该是用来监控任务变化的

