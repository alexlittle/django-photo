
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
        parser.add_argument('size', type=int)
        
        parser.add_argument(
            '-t',
            '--tag',
            dest='tag',
            help='filter on tag',
        )

    def handle(self, *args, **options):
        max_size = options['size']
        print options
        if options['tag']:
            photos = Photo.objects.filter(phototag__tag__name=options['tag']).exclude(thumbnailcache__size=max_size)
        else:
            photos = Photo.objects.exclude(thumbnailcache__size=max_size)
            
        print photos.count()
        for p in photos:
            print "processing: " + p.album.name + p.file
            print p.get_thumbnail(p,max_size)
        