from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('ukdata.views',
# rendered views
#    url(r'^$', 'maint'),
    url(r'^$', 'index'),
#    url(r'^test/$', 'index'),
#    url(r'^step09/$', 'step09'),
    url(r'^cpu/$', 'cpu'),
    url(r'^raw/$', 'raw'),
    url(r'^token/(?P<t>\S+)/$', 'token'),
    url(r'^site/(?P<sid>\S+)/$', 'site'),
    url(r'^sites.json$', 'rawbysite'),
#    url(r'^sites/(?P<id>\S+)/$', 'sitev2'),
    url(r'^update/$', 'update'),
    url(r'^toa/$', 'toa'),
    url(r'^localgroup/$', 'localgroup'),
    (r'^admin/', include(admin.site.urls)),
)
