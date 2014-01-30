from __future__ import unicode_literals, print_function
from django.conf import settings
from django.conf.urls import patterns, url
from .views import LazyMultiresImage


urlpatterns = patterns(
    '',
    url(r'^(?P<uuid>[0-9a-f]{32})/$',
        LazyMultiresImage.as_view(),
        name='lazy_multires'),
)
