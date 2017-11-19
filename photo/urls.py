# photo/urls.py
from django.conf import settings
from django.conf.urls import include, url

from photo import views as photo_views


urlpatterns = [
    url(r'^$', photo_views.home_view, name="photo_home"),
    url(r'^scan/$', photo_views.scan_folder, name="photo_scan"),
    url(r'^cloud/$', photo_views.cloud_view, name="photo_cloud"),
    url(r'^album/(?P<album_id>\d+)$', photo_views.album_view, name="photo_album"),
    url(r'^tag/(?P<tag_id>\d+)$', photo_views.tag_view, name="photo_tag"),
    url(r'^photo/view/(?P<photo_id>\d+)$', photo_views.photo_view, name="photo_view"),
    url(r'^photo/edit/(?P<photo_id>\d+)$', photo_views.photo_edit_view, name="photo_edit"),
    url(r'^photo/setcover/(?P<photo_id>\d+)$', photo_views.photo_set_cover, name="photo_set_cover"),
]
