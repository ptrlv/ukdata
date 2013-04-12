import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'ukdata.settings'

sys.path.append('/home/d0/love/projects')
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
