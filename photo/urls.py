
from django.urls import include, path

from photo import views as photo_views


urlpatterns = [
    path('', photo_views.home_view, name="photo_home"),
    path('map/', photo_views.map_view, name="photo_map"),
    path('scan/', photo_views.scan_folder, name="photo_scan"),
    path('cloud/', photo_views.cloud_view, name="photo_cloud"),
    path('cloud/<str:category>', photo_views.cloud_category_view, name="photo_cloud_category"),
    path('search/', photo_views.search_view, name="photo_search"),
    path('album/<int:album_id>', photo_views.album_view, name="photo_album"),
    path('album/<int:album_id>/exif', photo_views.album_exif, name="photo_album_exif"),
    path('tag/<str:slug>', photo_views.tag_slug_view, name="photo_tag_slug"),
    path('photo/view/<int:photo_id>', photo_views.photo_view, name="photo_view"),
    path('photo/edit/<int:photo_id>', photo_views.photo_edit_view, name="photo_edit"),
    path('photo/star/<int:photo_id>', photo_views.photo_star_view, name="photo_star"),
    path('photo/unstar/<int:photo_id>', photo_views.photo_unstar_view, name="photo_unstar"),
    path('photo/favourites/', photo_views.photo_favourites_view, name="photo_favourites"),

    path('photo/setcover/<int:photo_id>', photo_views.photo_set_cover, name="photo_set_cover"),
    path('album/updatetags/', photo_views.photo_update_tags, name="photo_update_tags"),

    path('export/', include('photo.export.urls')),
]
