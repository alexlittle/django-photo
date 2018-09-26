# photo/urls.py
from django.conf import settings
from django.conf.urls import include, url

from photo.export import views as photo_export

urlpatterns = [
    url(r'(?P<album_id>\d+)$', photo_export.make_view_pdf, name="photo_export_pdf"),
    url(r'^tag/(?P<slug>\w[\w/-]*)$', photo_export.tag_to_folder, name="photo_export_tag_to_folder"),
]