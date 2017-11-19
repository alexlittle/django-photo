
import base64
import datetime
import glob
import os
import pytz
import re

from io import BytesIO

from PIL import Image
from PIL.ExifTags import TAGS

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext_lazy as _

from photo.forms import ScanFolderForm, EditPhotoForm
from photo.models import Album, Photo, PhotoTag, Tag, ThumbnailCache

# Create your views here.


def home_view(request):
    albums = Album.objects.all().order_by('-name')
    return render(request, 'photo/home.html',
                              {'albums': albums,})
    
def album_view(request, album_id):
    album = Album.objects.get(pk=album_id)
    photos = Photo.objects.filter(album=album).order_by('date')
    for p in photos:
        p.tags = Tag.objects.filter(phototag__photo=p)
    
    return render(request, 'photo/album.html',
                               {'title': album.name,
                                'photos': photos})
    
def tag_view(request, tag_id):
    tag = Tag.objects.get(pk=tag_id)
    photos = Photo.objects.filter(phototag__tag=tag).order_by('date')
    for p in photos:
        p.tags = Tag.objects.filter(phototag__photo=p)
    return render(request, 'photo/album.html',
                               {'title': tag.name,
                                'photos': photos})

def tag_name_view(request, name):
    tag = Tag.objects.get(name=name)
    return redirect(tag_view, tag_id=tag.id)
     
def cloud_view(request):
    tags = Tag.objects.all().order_by('name')
    return render(request,'photo/cloud.html',
                               {'title': _('Cloud'),
                                'tags': tags})
       
def photo_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    image = settings.PHOTO_ROOT + photo.album.name + photo.file
    im = Image.open(image)
    response = HttpResponse(content_type="image/jpg")
    im.save(response, "JPEG")
    return response
      
def scan_folder(request):
    
    if request.method == 'POST':
        form = ScanFolderForm(request.POST)
        if form.is_valid(): # All validation rules pass
            directory = form.cleaned_data.get("directory") 
            default_tags = form.cleaned_data.get("default_tags")
            tags = [x.strip() for x in default_tags.split(',')]
            
            # find if dir is already in locations
            album, created = Album.objects.get_or_create(name=directory)
            
            # get all the image files from dir
            image_files = glob.glob(settings.PHOTO_ROOT + directory + "*.jpg")
            for im in image_files:
                image_file_name = os.path.basename(im)
                
                # find if image exists
                photo, created = Photo.objects.get_or_create(album=album, file=image_file_name)
                
                # add all the tags
                for t in tags:
                    tag, created = Tag.objects.get_or_create(name=t)
                    photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag= tag)
                 
                exif_tags, result = get_exif(im)
                if result:
                    exif_date = exif_tags['DateTimeOriginal'] 
                    naive = parse_datetime(re.sub(r'\:', r'-', exif_date, 2) )
                    photo.date = pytz.timezone("Europe/London").localize(naive, is_dst=None)
                    
                photo.save()
            
            return HttpResponseRedirect(reverse('photo_album', kwargs={'album_id': album.id }))     
    else:
        data = {}
        data['default_date'] = timezone.now()
        data['directory'] = '/photos/' + str(timezone.now().year) + '/'
        data['default_tags'] = ''
        form = ScanFolderForm(initial=data)

    return render(request, 'photo/scan.html', {'form': form,'title':_(u'Scan Folder')})



def photo_edit_view(request, photo_id):
    
    photo = Photo.objects.get(pk=photo_id)
    
    if request.method == 'POST':
        form = EditPhotoForm(request.POST)
        if form.is_valid(): # All validation rules pass
            
            # delete any existing tags
            PhotoTag.objects.filter(photo=photo).delete()
            
            new_tags = form.cleaned_data.get("tags")
            tags = [x.strip() for x in new_tags.split(',')]
            for t in tags:
                tag, created = Tag.objects.get_or_create(name=t)
                photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag= tag)
    
        return HttpResponseRedirect(reverse('photo_album', kwargs={'album_id': photo.album.id }))
     
    else:
        tags = Tag.objects.filter(phototag__photo=photo).values_list('name', flat=True)
        data = {}
        data['tags'] = ", ".join(tags)
        form = EditPhotoForm(initial=data)

    return render(request, 'photo/edit.html', {'form': form,'title':_(u'Edit Photo'), 'photo': photo})


def photo_set_cover(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    album = Album.objects.get(pk=photo.album.id)
    photos = Photo.objects.filter(album=album)
    for p in photos:
        p.album_cover = False
        p.save()
        
    
    photo.album_cover = True
    photo.save()
    
    return redirect('photo_album', album_id=album.id)
    
def get_exif(fn):
    ret = {}
    i = Image.open(fn)
    info = i._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[decoded] = value
        return ret, True
    else:
        return None, False