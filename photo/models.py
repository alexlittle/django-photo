from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from tastypie.models import create_api_key

models.signals.post_save.connect(create_api_key, sender=User)

class Location (models.Model):
    name = models.TextField(blank=False, null=False)
    
class Photo (models.Model):
    file = models.TextField(blank=False, null=False)
    date = models.DateTimeField(default=timezone.now)
    location = models.ForeignKey(Location)   
    
class Tag (models.Model):
    name = models.TextField(blank=False, null=False)

class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo)
    tag = models.ForeignKey(Tag)