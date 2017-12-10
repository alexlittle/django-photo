import hashlib
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from io import BytesIO

from PIL import Image

from photo.cache_storage import ImageCacheFileSystemStorage

class Album (models.Model):
    name = models.TextField(blank=False, null=False)
    title = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Album')
        verbose_name_plural = _('Album')
        
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
    
    class Meta:
        verbose_name = _('Photo')
        verbose_name_plural = _('Photos')
        
    @staticmethod
    def get_thumbnail(photo,max_size):
        try:
            print photo.id, max_size
            thumb = ThumbnailCache.objects.filter(photo=photo, size=max_size)[:1].get()
        except ThumbnailCache.DoesNotExist:
            try: 
                image = settings.PHOTO_ROOT + photo.album.name + photo.file
                im = Image.open(image)
                im.thumbnail((int(max_size),int(max_size)), Image.ANTIALIAS)        
                buffer = BytesIO()
                im.save(fp=buffer, format='JPEG')
                pillow_image = ContentFile(buffer.getvalue())
                file_name = hashlib.md5(buffer.getvalue()).hexdigest()
                thumb = ThumbnailCache(size=max_size, photo=photo, image=InMemoryUploadedFile(
                                                                                     pillow_image,       # file
                                                                                     None,               # field_name
                                                                                     file_name,           # file name
                                                                                     'image/jpeg',       # content_type
                                                                                     pillow_image.tell,  # size
                                                                                     None)               # content_type_extra
                                       )
                thumb.save()
            except IOError:
                return None 
           
        return thumb.image.url


class TagCategory(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Tag Category')
        verbose_name_plural = _('Tag Categories')
         
class Tag (models.Model):
    name = models.TextField(blank=False, null=False)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    tagcategory  = models.ForeignKey(TagCategory,null=True,default=None)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        
class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo)
    tag = models.ForeignKey(Tag)
 
    class Meta:
        verbose_name = _('Photo Tag')
        verbose_name_plural = _('Photo Tags')
        
def image_file_name(instance, filename):
        basename, ext = os.path.splitext(filename)
        return os.path.join('cache', filename[0:2], filename[2:4], filename + ext.lower())   
    
class ThumbnailCache(models.Model):
    photo = models.ForeignKey(Photo)
    size = models.IntegerField(blank=False, null=False) 
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True) 
    image = models.ImageField(upload_to=image_file_name,  blank=True, null=True)
    
    class Meta:
        verbose_name = _('Thumbnail Cache')
        verbose_name_plural = _('Thumbnail Caches')
    
    
    
    