
import base64

from PIL import Image

from django.conf import settings
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from django.utils import timezone
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
      
def scan_folder(request):
    
    if request.method == 'POST':
        form = ScanFolderForm(request.POST)
        if form.is_valid(): # All validation rules pass
            
            
            pass
    else:
        data = {}
        data['default_date'] = timezone.now()
        data['directory'] = '/photo/'
        data['default_tags'] = 'test'
        form = ScanFolderForm(initial=data)

    return render(request, 'photo/scan.html', {'form': form,'title':_(u'Scan Folder')})