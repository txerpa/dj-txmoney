from __future__ import absolute_import, unicode_literals

from django.conf.urls import patterns, url

from tests.testapp.views import *

urlpatterns = patterns(
    '',
    url(r'^instance-view/$', instance_view),
    url(r'^model-view/$', model_view),
    url(r'^model-save-view/(?P<amount>\S+)/(?P<currency>\S+)/$', model_from_db_view),
)
