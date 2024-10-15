
from django.urls import include, path

from photo import views as p_views

app_name = 'photo'

urlpatterns = [
    path('', p_views.home_view, name="home"),
    path('map/', p_views.map_view, name="map"),
    path('scan/', p_views.scan_folder, name="scan"),
    path('cloud/', p_views.cloud_view, name="cloud"),
    path('cloud/<str:category>', p_views.cloud_category_view, name="cloud_category"),
    path('search/', p_views.search_view, name="search"),
    path('album/<int:album_id>', p_views.AlbumView.as_view(), name="album"),
    path('album/<int:album_id>/exif', p_views.album_exif, name="album_exif"),
    path('tag/<str:slug>', p_views.tag_slug_view, name="tag_slug"),
    path('photo/view/<int:photo_id>.jpg', p_views.photo_view, name="view"),
    path('photo/edit/<int:photo_id>', p_views.photo_edit_view, name="edit"),
    path('photo/star/<int:photo_id>', p_views.photo_star_view, name="star"),
    path('photo/unstar/<int:photo_id>', p_views.photo_unstar_view, name="unstar"),
    path('photo/favourites/', p_views.photo_favourites_view, name="favourites"),

    path('photo/view/annotated/<int:photo_id>.jpg', p_views.PhotoViewAnnotated.as_view(), name="view_annotated"),

    path('photo/setcover/<int:photo_id>', p_views.photo_set_cover, name="set_cover"),
    path('album/updatetags/', p_views.photo_update_tags, name="update_tags"),

    path('export/', include('photo.export.urls')),
    path('scan/async', p_views.scan_folder_async, name='scan_folder_async'),
]
