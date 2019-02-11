
"""
Management command to pre-cache thumbnail images
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Photo, ThumbnailCache

class Command(BaseCommand):
    help = "Pre-caches thumbnail images"


    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--size',
            dest='size',
            type=int)
        
        parser.add_argument(
            '-t',
            '--tag',
            dest='tag',
            help='filter on tag',
        )

    def handle(self, *args, **options):
        if options['size']:
            sizes = [options['size']]
        else:
            sizes = [settings.ALBUM_COVER_THUMBNAIL_SIZE, 
                     settings.PHOTO_DEFAULT_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_PDF_SIZE]
            
        for size in sizes:
            if options['tag']:
                photos = Photo.objects.filter(phototag__tag__name=options['tag']).exclude(thumbnailcache__size=size)
            else:
                photos = Photo.objects.exclude(thumbnailcache__size=size)
                
            print(str(photos.count()) + " to process")
            
            for p in photos:
                print("processing: " + p.album.name + p.file)
                thumb_cache = p.get_thumbnail(p,size)
                if thumb_cache:
                    print(p.get_thumbnail(p,size))
                else:
                    return
        