
"""
Management command to redate photos
"""
import os
import pytz
import re
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from photo.models import Photo, ThumbnailCache, Album

from photo.views import get_exif

class Command(BaseCommand):
    help = "Redates photos"


    def add_arguments(self, parser):        
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def handle(self, *args, **options):
        try:
            album = Album.objects.get(id=options['album'])
        except Album.DoesNotExist:
            print("No Album Specified")
            return
        
        print("Updating dates for... " + album.name)
        photos = Photo.objects.filter(album=album)
        
        for photo in photos:
            im = settings.PHOTO_ROOT + album.name + photo.file
            exif_tags, result = get_exif(im)
            if result:
                try:
                    if 'DateTimeOriginal' in exif_tags:
                        exif_date = exif_tags['DateTimeOriginal'] 
                    elif 'DateTimeDigitized' in exif_tags:
                        exif_date = exif_tags['DateTimeDigitized'] 
                    elif 'DateTime' in exif_tags:
                        exif_date = exif_tags['DateTime'] 
                    naive = parse_datetime(re.sub(r'\:', r'-', exif_date, 2) )
                    photo.date = pytz.timezone("Europe/London").localize(naive, is_dst=None)
                    photo.save()
                    print("updated: " + photo.file)
                except KeyError:
                    print(exif_tags) 
                    print("KeyError"  + photo.file)
                except AttributeError:
                    print("AttributeError " + photo.file)
                except ValueError:
                    print("ValueError " + photo.file)
        