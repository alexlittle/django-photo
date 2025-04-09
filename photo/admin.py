from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from photo.lib import rename_photo_file
from photo.models import Album, Photo, Tag, PhotoTag, TagCategory, PhotoProps, TagProps


class AlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'view_url', 'count', 'title', 'date_display')
    search_fields = ['name', 'title', 'date_display']

    def view_url(self, obj):
        return format_html("<a href="+reverse('photo:album', args={obj.id}) + ">View</a>")

    def count(self, obj):
        return Photo.objects.filter(album=obj).count()

    view_url.short_description = "View"


class PhotoPropsInline(admin.TabularInline):
    model = PhotoProps


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('file', 'date', 'edit_photo', 'title', 'album', 'albumid')
    search_fields = ['file', 'title']
    actions = ['rename_file']

    def edit_photo(self, obj):
        return format_html("<a target='_blank' href="+reverse('photo:edit', args={obj.id}) + ">Edit</a>")

    def albumid(self, obj):
        return obj.album.id

    def rename_file(self, request, queryset):
        for photo in queryset:
            rename_photo_file(photo)

    inlines = [
        PhotoPropsInline,
    ]


class TagPropsInline(admin.TabularInline):
    model = TagProps


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'view_url', 'tagcategory', 'slug')
    search_fields = ['name']
    actions = ['mark_category_place',
               'mark_category_person',
               'mark_category_animal',
               'mark_category_date',
               'mark_category_object',
               'mark_category_food',
               'mark_category_event',
               'mark_category_activity',
               'mark_category_organisation',
               'mark_category_label', ]
    inlines = [
        TagPropsInline,
    ]

    def view_url(self, obj):
        return format_html("<a href="+reverse('photo:tag_slug', args={obj.slug}) + ">View</a>")

    view_url.short_description = "View"

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

    def mark_category_label(self, request, queryset):
        tc = TagCategory.objects.get(name='Label')
        queryset.update(tagcategory=tc)


class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ['name']


class PhotoTagAdmin(admin.ModelAdmin):
    list_display = ('photo', 'tag')


class PhotoPropsAdmin(admin.ModelAdmin):
    list_display = ('photo', 'name', 'value')


class TagPropsAdmin(admin.ModelAdmin):
    list_display = ('tag', 'name', 'value')


admin.site.register(Album, AlbumAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(PhotoTag, PhotoTagAdmin)
admin.site.register(TagCategory, TagCategoryAdmin)
admin.site.register(PhotoProps, PhotoPropsAdmin)
admin.site.register(TagProps, TagPropsAdmin)
