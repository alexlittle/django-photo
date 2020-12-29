
"""
Management command to add tags based on filename
"""
import pytz
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Photo, Album, Tag, PhotoTag


class Command(BaseCommand):
    help = "add tags based on filename"

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
        
        photos = Photo.objects.filter(album=album)
        for photo in photos:
            new_tag = photo.file.split('.')[0].replace('-',' ').replace('_',' ')
            res = re.sub(r'\d', '', new_tag).strip() 
            print(res)
            tag, created = Tag.objects.get_or_create(name=res)
            photo_tag, created = PhotoTag.objects.get_or_create(
                photo=photo, tag=tag)
            print('http://localhost.photo' + reverse('photo_edit', kwargs={'photo_id':
                                                photo.id}))
            
            