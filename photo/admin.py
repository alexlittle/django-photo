from django.contrib import admin

# Register your models here.
from photo.models import Album, Photo, Tag, PhotoTag, TagCategory, ThumbnailCache, PhotoProps, TagProps

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    search_fields = ['name','title']
  
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('file', 'date', 'album')  
    search_fields = ['file']
    
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'tagcategory')  
    search_fields = ['name']
    actions = ['mark_category_place', 
               'mark_category_person', 
               'mark_category_animal',
               'mark_category_date',
               'mark_category_object',
               'mark_category_food',
               'mark_category_event',
               'mark_category_activity',
               'mark_category_organisation',]

    def mark_category_place(self, request, queryset):
        tc = TagCategory.objects.get(name='Place')
        queryset.update(tagcategory=tc)
    
    def mark_category_person(self, request, queryset):
        tc = TagCategory.objects.get(name='Person')
        queryset.update(tagcategory=tc)
        
    def mark_category_animal(self, request, queryset):
        tc = TagCategory.objects.get(name='Animal')
        queryset.update(tagcategory=tc)
        
    def mark_category_date(self, request, queryset):
        tc = TagCategory.objects.get(name='Date')
        queryset.update(tagcategory=tc)
    
    def mark_category_object(self, request, queryset):
        tc = TagCategory.objects.get(name='Object')
        queryset.update(tagcategory=tc)
        
    def mark_category_food(self, request, queryset):
        tc = TagCategory.objects.get(name='Food')
        queryset.update(tagcategory=tc)
    
    def mark_category_event(self, request, queryset):
        tc = TagCategory.objects.get(name='Event')
        queryset.update(tagcategory=tc)
        
    def mark_category_activity(self, request, queryset):
        tc = TagCategory.objects.get(name='Activity')
        queryset.update(tagcategory=tc)
        
    def mark_category_organisation(self, request, queryset):
        tc = TagCategory.objects.get(name='Organisation')
        queryset.update(tagcategory=tc)
    
    
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )  
    search_fields = ['name']
       
class PhotoTagAdmin(admin.ModelAdmin):
    list_display = ('photo', 'tag')      

class ThumbnailCacheAdmin(admin.ModelAdmin):
    list_display = ('photo', 'size', 'image') 
    search_fields = ['photo', 'image']
 
class PhotoPropsAdmin(admin.ModelAdmin):
    list_display = ('photo', 'name', 'value')   
 
class TagPropsAdmin(admin.ModelAdmin):
    list_display = ('tag', 'name', 'value') 
          
admin.site.register(Album, AlbumAdmin)   
admin.site.register(Photo, PhotoAdmin)  
admin.site.register(Tag, TagAdmin)  
admin.site.register(PhotoTag, PhotoTagAdmin)  
admin.site.register(TagCategory, TagCategoryAdmin)  
admin.site.register(ThumbnailCache, ThumbnailCacheAdmin)
admin.site.register(PhotoProps, PhotoPropsAdmin)
admin.site.register(TagProps, TagPropsAdmin)


