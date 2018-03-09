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

from .fields import AutoSlugField

class Album (models.Model):
    name = models.TextField(blank=False, null=False)
    slug = AutoSlugField(populate_from='name', max_length=200, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Album')
        verbose_name_plural = _('Album')
    
    def has_cover(self): 
        try:
            p = Photo.objects.get(album=self,album_cover=True)
        except Photo.DoesNotExist:
            return False
        return True
       
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

class TagCategory(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    slug = AutoSlugField(populate_from='name', max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Tag Category')
        verbose_name_plural = _('Tag Categories')
         
class Tag (models.Model):
    name = models.TextField(blank=False, null=False)
    slug = AutoSlugField(populate_from='name', max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    tagcategory  = models.ForeignKey(TagCategory,null=True,default=None)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        
    def get_prop(self, property):
        try:
            tag_prop = TagProps.objects.get(tag=self,name=property)
            return tag_prop.value
        except TagProps.DoesNotExist:
            return None
        
    def get_lat(self):
        return self.get_prop('lat')
    
    def get_lng(self):
        return self.get_prop('lng')
    
class Photo (models.Model):
    file = models.TextField(blank=False, null=False)
    slug = AutoSlugField(populate_from='file', max_length=100, blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    album = models.ForeignKey(Album) 
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)  
    album_cover = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, through='PhotoTag', name='tags' )
    
    def __unicode__(self):
        return self.file
    
    class Meta:
        verbose_name = _('Photo')
        verbose_name_plural = _('Photos')
    
    def get_prop(self, property):
        try:
            photo_prop = PhotoProps.objects.get(photo=self,name=property)
            return photo_prop.value
        except PhotoProps.DoesNotExist:
            return None
        
        
    @staticmethod
    def get_thumbnail(photo,max_size):
        try:
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

class PhotoProps(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = _('Photo property')
        verbose_name_plural = _('Photo properties')
        
class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag,  on_delete=models.CASCADE)
 
    class Meta:
        verbose_name = _('Photo Tag')
        verbose_name_plural = _('Photo Tags')
        
class TagProps(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = _('Tag property')
        verbose_name_plural = _('Tag properties')
        
def image_file_name(instance, filename):
        basename, ext = os.path.splitext(filename)
        return os.path.join('cache', filename[0:2], filename[2:4], filename + ext.lower())   
    
class ThumbnailCache(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    size = models.IntegerField(blank=False, null=False) 
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True) 
    image = models.ImageField(upload_to=image_file_name,  blank=True, null=True)
    
    class Meta:
        verbose_name = _('Thumbnail Cache')
        verbose_name_plural = _('Thumbnail Caches')
    
    
    
    