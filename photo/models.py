
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from io import BytesIO

from PIL import Image

class Album (models.Model):
    name = models.TextField(blank=False, null=False)
    title = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
    @staticmethod
    def get_cover(album,max_size):
        try:
            p = Photo.objects.get(album=album,album_cover=True)
        except Photo.DoesNotExist:
            try:
                p = Photo.objects.filter(album=album).earliest('date')
            except Photo.DoesNotExist:
                return None
            
        return p.get_thumbnail(p,max_size)
    
class Photo (models.Model):
    file = models.TextField(blank=False, null=False)
    date = models.DateTimeField(default=timezone.now)
    album = models.ForeignKey(Album) 
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)  
    album_cover = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.file
    
    @staticmethod
    def get_thumbnail(photo,max_size):
        try:
            thumb = ThumbnailCache.objects.get(photo=photo, size=max_size)
        except ThumbnailCache.DoesNotExist:
            image = settings.PHOTO_ROOT + photo.album.name + photo.file
            im = Image.open(image)
            im.thumbnail((int(max_size),int(max_size)), Image.ANTIALIAS)        
            buffer = BytesIO()
            im.save(fp=buffer, format='JPEG')
            pillow_image = ContentFile(buffer.getvalue())
    
            thumb = ThumbnailCache(size=max_size, photo=photo, image=InMemoryUploadedFile(
                                                                                 pillow_image,       # file
                                                                                 None,               # field_name
                                                                                 photo.file,           # file name
                                                                                 'image/jpeg',       # content_type
                                                                                 pillow_image.tell,  # size
                                                                                 None)               # content_type_extra
                                   )
            thumb.save()
           
        return thumb.image.url
    
class Tag (models.Model):
    name = models.TextField(blank=False, null=False)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
    
class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo)
    tag = models.ForeignKey(Tag)
    
    
class ThumbnailCache(models.Model):
    photo = models.ForeignKey(Photo)
    size = models.IntegerField(blank=False, null=False) 
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True) 
    image = models.ImageField(upload_to='thumbcache/%Y/%m/%d', max_length=200, blank=True, null=True)