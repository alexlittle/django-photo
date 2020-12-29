
"""
Management command to rewrite exif data
"""
import pytz
import re
import json

from PIL import Image
from PIL.ExifTags import TAGS
import io
import piexif

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Photo, Album, Tag, PhotoTag
from photo.lib import rewrite_exif

class Command(BaseCommand):
    help = "rewrites exif data to photos"

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def dict_to_binary(self, the_dict):
        my_json = json.dumps(the_dict)
        binary = ' '.join(format(ord(letter), 'b') for letter in my_json)
        return binary
    
    def handle(self, *args, **options):
        try:
            album = Album.objects.get(id=options['album'])
        except Album.DoesNotExist:
            print("No Album Specified")
            return
        
        photos = Photo.objects.filter(album=album)
        for photo in photos:
            print(photo)
            rewrite_exif(photo)
            
            
            