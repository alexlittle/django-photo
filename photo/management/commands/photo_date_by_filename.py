import os
import pytz
import re
import time 
import django.db.models
import datetime

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
        parser.add_argument('date')       
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )
        
    def handle(self, *args, **options):
        date = options['date'].split('-')
        year = date[0]
        month = date[1]
        day = date[2]
        album = Album.objects.get(pk=options['album'])
        photos = Photo.objects.filter(date__year=year, date__month=month, date__day=day, album=album)
    
        for photo in photos:
            new_year = int(photo.file[4:8])
            new_month = int(photo.file[8:10])
            new_day = int(photo.file[10:12])
            new_date = datetime.date(new_year,new_month,new_day)
            print(new_date)
            photo.date = new_date
            photo.save()