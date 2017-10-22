
import base64
import datetime
import glob
import os
import pytz
import re

from PIL import Image
from PIL.ExifTags import TAGS

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext_lazy as _

from photo.forms import ScanFolderForm
from photo.models import Location, Photo, PhotoTag, Tag

# Create your views here.


def home_view(request):
    locations = Location.objects.all().order_by('-name')
    return render_to_response('photo/home.html',
                              {'locations': locations,},
                              context_instance=RequestContext(request))
    
def location_view(request, location_id):
    location = Location.objects.get(pk=location_id)
    photos = Photo.objects.filter(location=location).order_by('date')
    for p in photos:
        p.tags = Tag.objects.filter(phototag__photo=p)
    
    return render_to_response('photo/set.html',
                               {'title': location.name,
                                'photos': photos},
                              context_instance=RequestContext(request))
  
def tag_view(request, tag_id):
    tag = Tag.objects.get(pk=tag_id)
    photos = Photo.objects.filter(phototag__tag=tag).order_by('date')
    for p in photos:
        p.tags = Tag.objects.filter(phototag__photo=p)
    return render_to_response('photo/set.html',
                               {'title': tag.name,
                                'photos': photos},
                              context_instance=RequestContext(request))
 
def cloud_view(request):
    tags = Tag.objects.all().order_by('name')
    return render_to_response('photo/cloud.html',
                               {'title': _('Cloud'),
                                'tags': tags},
                              context_instance=RequestContext(request))
       
def thumbnail_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    image = settings.PHOTO_ROOT + photo.location.name + photo.file
    im = Image.open(image)
    im.thumbnail(size=(200,200))
    response = HttpResponse(content_type="image/jpg")
    im.save(response, "JPEG")
    return response

def photo_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    image = settings.PHOTO_ROOT + photo.location.name + photo.file
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
            location, created = Location.objects.get_or_create(name=directory)
            
            # get all the image files from dir
            image_files = glob.glob(settings.PHOTO_ROOT + directory + "*.jpg")
            for im in image_files:
                image_file_name = os.path.basename(im)
                
                # find if image exists
                photo, created = Photo.objects.get_or_create(location=location, file=image_file_name)
                
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
            
            return HttpResponseRedirect(reverse('photo_location', kwargs={'location_id': location.id }))     
    else:
        data = {}
        data['default_date'] = timezone.now()
        data['directory'] = '/photos/' + str(timezone.now().year) + '/'
        data['default_tags'] = ''
        form = ScanFolderForm(initial=data)

    return render(request, 'photo/scan.html', {'form': form,'title':_(u'Scan Folder')})



def photo_edit_view(request, photo_id):
    
    
    return

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