import os
import pytz
import re
import time 
import django.db.models
import datetime

from optparse import make_option

from shutil import copy

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from photo.models import Photo, ThumbnailCache, Album, Tag

from photo.views import get_exif

class Command(BaseCommand):
    help = "Exports tag photos"


    def add_arguments(self, parser): 
        parser.add_argument('tag')       
        
    def handle(self, *args, **options):
        tag = Tag.objects.get(slug=options['tag'])
        photos = Photo.objects.filter(phototag__tag=tag)
        
        export_path = os.path.join(settings.PHOTO_ROOT,'export',tag.slug)
        try:
            os.makedirs(export_path)
        except OSError:
            print("couldn't create directory - maybe it already exists?")
        
        for photo in photos:
            file_to_copy = os.path.join(settings.PHOTO_ROOT, photo.album.name[1:], photo.file)
            print(os.path.join(settings.PHOTO_ROOT, photo.album.name[1:], photo.file))
            copy(file_to_copy, export_path)
        