
from django.urls import include, path

from photo import views as photo_views

app_name = 'photo'

urlpatterns = [
    path('', photo_views.HomeView.as_view(), name="home"),
    path('map/', photo_views.MapView.as_view(), name="map"),
    path('scan/', photo_views.ScanFolderView.as_view(), name="scan"),
    path('cloud/', photo_views.CloudView.as_view(), name="cloud"),
    path('cloud/<str:category>/', photo_views.CloudCategoryView.as_view(), name="cloud_category"),
    path('search/', photo_views.SearchView.as_view(), name="search"),
    path('album/<int:album_id>/', photo_views.AlbumView.as_view(), name="album"),
    path('album/<int:album_id>/exif/', photo_views.AlbumExifUpdateView.as_view(), name="album_exif"),
    path('tag/<str:slug>/', photo_views.TagSlugView.as_view(), name="tag_slug"),
    path('photo/view/<int:photo_id>.jpg', photo_views.PhotoView.as_view(), name="view"),
    path('photo/edit/<int:photo_id>/', photo_views.PhotoEditView.as_view(), name="edit"),
    path('photo/star/<int:photo_id>/', photo_views.PhotoStarView.as_view(), name="star"),
    path('photo/unstar/<int:photo_id>/', photo_views.PhotoUnstarView.as_view(), name="unstar"),
    path('photo/favourites/', photo_views.PhotoFavouritesView.as_view(), name="favourites"),

    path('photo/view/annotated/<int:photo_id>.jpg', photo_views.PhotoViewAnnotated.as_view(), name="view_annotated"),

    path('photo/setcover/<int:photo_id>/', photo_views.PhotoSetCoverView.as_view(), name="set_cover"),
    path('album/updatetags/', photo_views.PhotoUpdateTagsView.as_view(), name="update_tags"),

    path('export/', include('photo.export.urls')),
    path('scan/async/', photo_views.ScanFolderAsyncView.as_view(), name='scan_folder_async'),
]
