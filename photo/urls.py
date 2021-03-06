
from django.conf.urls import include, url

from photo import views as photo_views


urlpatterns = [
    url(r'^$', photo_views.home_view, name="photo_home"),
    url(r'^map/$', photo_views.map_view, name="photo_map"),
    url(r'^scan/$', photo_views.scan_folder, name="photo_scan"),
    url(r'^cloud/$', photo_views.cloud_view, name="photo_cloud"),
    url(r'^cloud/(?P<category>\w+)$',
        photo_views.cloud_category_view, name="photo_cloud_category"),
    url(r'^search/$', photo_views.search_view, name="photo_search"),
    url(r'^album/(?P<album_id>\d+)$',
        photo_views.album_view,
        name="photo_album"),
    url(r'^album/(?P<album_id>\d+)/exif$',
        photo_views.album_exif,
        name="photo_album_exif"),
    url(r'^tag/(?P<slug>\w[\w/-]*)$',
        photo_views.tag_slug_view, name="photo_tag_slug"),
    url(r'^photo/view/(?P<photo_id>\d+)$',
        photo_views.photo_view, name="photo_view"),
    url(r'^photo/edit/(?P<photo_id>\d+)$',
        photo_views.photo_edit_view, name="photo_edit"),
    url(r'^photo/star/(?P<photo_id>\d+)$',
        photo_views.photo_star_view, name="photo_star"),
    url(r'^photo/unstar/(?P<photo_id>\d+)$',
        photo_views.photo_unstar_view, name="photo_unstar"),
    url(r'^photo/favourites/$', photo_views.photo_favourites_view,
        name="photo_favourites"),

    url(r'^photo/setcover/(?P<photo_id>\d+)$',
        photo_views.photo_set_cover, name="photo_set_cover"),
    url(r'^album/updatetags/$',
        photo_views.photo_update_tags, name="photo_update_tags"),

    url(r'^export/', include('photo.export.urls')),
]
