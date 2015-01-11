from django.shortcuts import render,render_to_response
from django.template import RequestContext

from django.utils.translation import ugettext_lazy as _

from photo.forms import ScanFolderForm
# Create your views here.


def home_view(request):
    
    return render_to_response('photo/home.html',
                              context_instance=RequestContext(request))
    
    
def scan_folder(request):
    
    if request.method == 'POST':
        form = ScanFolderForm(request.POST)
        if form.is_valid(): # All validation rules pass
            pass
    else:
        form = ScanFolderForm() # An unbound form

    return render(request, 'photo/scan.html', {'form': form,'title':_(u'Scan Folder')})