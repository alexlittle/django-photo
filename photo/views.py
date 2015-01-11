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
    locations = Location.objects.all()
    return render_to_response('photo/home.html',
                              context_instance=RequestContext(request))
    
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