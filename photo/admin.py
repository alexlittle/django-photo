from django.contrib import admin

# Register your models here.
from photo.models import Album, Photo, Tag, PhotoTag

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
  
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('file', 'date', 'album')  
    
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )  
        
class PhotoTagAdmin(admin.ModelAdmin):
    list_display = ('photo', 'tag')      


admin.site.register(Album, AlbumAdmin)   
admin.site.register(Photo, PhotoAdmin)  
admin.site.register(Tag, TagAdmin)  
admin.site.register(PhotoTag, PhotoTagAdmin)  