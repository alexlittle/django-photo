from django.urls import path

from photo.export import views as photo_export

urlpatterns = [
    path('<int:album_id>', photo_export.make_view_pdf, name="export_pdf"),
    path('tag/<str:slug>', photo_export.tag_to_folder, name="export_tag_to_folder"),
]
