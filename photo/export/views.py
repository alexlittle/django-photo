
from shutil import copy2

from django.conf import settings
from django.http import HttpResponse, FileResponse, HttpResponseRedirect

from photo.models import Photo, Tag
from photo.export import create_album

def make_view_pdf(request, album_id):
    album_url = create_album.make(album_id)
    response = FileResponse(open(album_url, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = "inline; filename=export-album"+ str(album_id) + ".pdf"
    return response

def tag_to_folder(request, slug):
    dest = "/home/alex/Downloads/pauliina/"
    tag = Tag.objects.get(slug=slug)
    photos = Photo.objects.filter(phototag__tag=tag)
    for photo in photos:
        copy2(settings.PHOTO_ROOT + photo.album.name + photo.file, dest)
    return HttpResponseRedirect(reverse('photo_tag_slug', kwargs={'slug': slug }))    
    