
"""
Management command to clean up any albums with no photos
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Photo, Album

class Command(BaseCommand):
    help = "Removes any albums with no photos"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        albums = Album.objects.filter(photo=None)
        for a in albums:
            print "Removing: " + a.name
            a.delete()
        