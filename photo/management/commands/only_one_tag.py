
"""
Management command to find photos with only one tag
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Album, Photo, PhotoTag


class bcolors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        albums = Album.objects.all().order_by('name')
        
        total_count = 0
        for album in albums:
            
            photos = Photo.objects.filter(album=album)

            for photo in photos:
                tag_count = PhotoTag.objects.filter(photo=photo).count()
                if tag_count < 2:
                    print(album.name + photo.file)
                    total_count += 1
                    
        print(total_count)