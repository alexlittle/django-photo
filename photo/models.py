
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from PIL import Image

class Location (models.Model):
    name = models.TextField(blank=False, null=False)
    title = models.TextField(blank=True, null=True)
    
class Photo (models.Model):
    file = models.TextField(blank=False, null=False)
    date = models.DateTimeField(default=timezone.now)
    location = models.ForeignKey(Location)   
    
class Tag (models.Model):
    name = models.TextField(blank=False, null=False)

class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo)
    tag = models.ForeignKey(Tag)