
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

    def handle(self, *args, **options):
        albums = Album.objects.filter(photo__date__gte="2019-01-01", photo__date__lte="2019-12-31").distinct().order_by('name')
        for album in albums:
            print(album.name + " - " + str(album.id))
            
            