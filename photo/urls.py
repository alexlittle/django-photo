# photo/urls.py
from django.conf import settings
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',

    url(r'^$', 'photo.views.home_view', name="photo_home"),
    url(r'^scan/$', 'photo.views.scan_folder', name="photo_scan"),
    url(r'^location/(?P<location_id>\d+)$', 'photo.views.location_view', name="photo_location"),
    url(r'^thumbnail/(?P<photo_id>\d+)$', 'photo.views.thumbnail_view', name="photo_thumbnail"),
    url(r'^tag/(?P<tag_id>\d+)$', 'photo.views.tag_view', name="photo_tag"),
)
