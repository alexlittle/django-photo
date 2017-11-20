from django.contrib import admin

# Register your models here.
from photo.models import Album, Photo, Tag, PhotoTag, TagCategory, ThumbnailCache

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    search_fields = ['name','title']
  
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('file', 'date', 'album')  
    search_fields = ['file']
    
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'tagcategory')  
    search_fields = ['name']
    
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )  
    search_fields = ['name']
       
class PhotoTagAdmin(admin.ModelAdmin):
    list_display = ('photo', 'tag')      

class ThumbnailCacheAdmin(admin.ModelAdmin):
    list_display = ('photo', 'size', 'image') 
    search_fields = ['photo', 'image']
    
admin.site.register(Album, AlbumAdmin)   
admin.site.register(Photo, PhotoAdmin)  
admin.site.register(Tag, TagAdmin)  
admin.site.register(PhotoTag, PhotoTagAdmin)  
admin.site.register(TagCategory, TagCategoryAdmin)  
admin.site.register(ThumbnailCache, ThumbnailCacheAdmin)

