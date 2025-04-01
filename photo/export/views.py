import os
import shutil

from django.conf import settings
from django.urls import reverse
from django.views import View
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect

from photo.models import Photo, Tag, Album
from photo.export import create_album


class MakeViewPDF(View):
    def get(self, request, album_id):
        """Generate and return a PDF for the given album."""
        album = get_object_or_404(Album, id=album_id)  # Ensure album exists
        album_url = create_album.make(album_id)  # Generate PDF file path

        if not os.path.exists(album_url):  # Handle missing file
            raise Http404("PDF file not found")

        response = FileResponse(open(album_url, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=export-album{album_id}.pdf'
        return response


class TagToFolderView(View):
    def post(self, request, slug):
        """Copy all photos tagged with `slug` into a folder."""
        dest = os.path.join(settings.PHOTO_ROOT, "export", slug)
        os.makedirs(dest, exist_ok=True)

        tag = get_object_or_404(Tag, slug=slug)
        photos = Photo.objects.filter(phototag__tag=tag)

        for photo in photos:
            src = os.path.join(settings.PHOTO_ROOT, photo.album.name.lstrip("/"), photo.file)
            shutil.copy2(src, dest)  # Preserve metadata

        return redirect(reverse('photo:tag_slug', kwargs={'slug': slug}))
