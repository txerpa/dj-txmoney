from django.conf.urls import patterns, url

from tests.testapp.views import *

urlpatterns = patterns(
    '',
    url(r'^instance-view/$', instance_view),
    url(r'^model-view/$', model_view),
    url(r'^model-save-view/(?P<amount>\S+)/(?P<currency>\S+)/$', model_from_db_view),
    url(r'^model-form-view/(?P<amount>\S+)/(?P<currency>\S+)/$', model_form_view),
    url(r'^regular_form/$', regular_form),
    url(r'^regular_form/(?P<id>\d+)/$', regular_form_edit),
    url(r'^model_form/(?P<id>\d+)/$', model_form_edit),
)
