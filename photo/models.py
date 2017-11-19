
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from PIL import Image

class Album (models.Model):
    name = models.TextField(blank=False, null=False)
    title = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
class Photo (models.Model):
    file = models.TextField(blank=False, null=False)
    date = models.DateTimeField(default=timezone.now)
    album = models.ForeignKey(Album) 
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)  
    
    def __unicode__(self):
        return self.file
    
class Tag (models.Model):
    name = models.TextField(blank=False, null=False)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
    
class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo)
    tag = models.ForeignKey(Tag)