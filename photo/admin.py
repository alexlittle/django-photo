from django.contrib import admin

# Register your models here.
from photo.models import Location, Photo, Tag, PhotoTag

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
  
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('file', 'date', 'location')  
    
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )  
        
class PhotoTagAdmin(admin.ModelAdmin):
    list_display = ('photo', 'tag')      


admin.site.register(Location, LocationAdmin)   
admin.site.register(Photo, PhotoAdmin)  
admin.site.register(Tag, TagAdmin)  
admin.site.register(PhotoTag, PhotoTagAdmin)  