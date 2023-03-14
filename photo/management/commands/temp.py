
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

from photo.models import Photo, Album, Tag, TagCategory, ThumbnailCache
from . import bcolors


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        photos = Photo.objects.filter(album__id=1436)
        
        #remove existing thumbs
        ThumbnailCache.objects.filter(photo__in=photos).delete()
        call_command('files_pre_cache_thumbnails')
        
        for p in photos:
            print("----------------------------------------------")
            print("%s%s - %sphoto/edit/%d" % (p.album.name, p.file, settings.DOMAIN_NAME, p.id))
            cache = ThumbnailCache.objects.filter(photo=p)
            for c in cache:
                print("%s%s" % (settings.DOMAIN_NAME, c.image.url))
            print("-")