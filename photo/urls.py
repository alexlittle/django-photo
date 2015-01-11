# photo/urls.py
from django.conf import settings
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',

    url(r'^$', 'photo.views.home_view', name="photo_home"),
    
)
