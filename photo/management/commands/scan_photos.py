
"""
Management command to find any photos that haven't been uploaded
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Album, Photo

class bcolors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class Command(BaseCommand):
    help = "Checks for photos that aren't in the database"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        paths = ['photos', 'negatives']
       
        ignore_extensions = ['.avi', '.cr2', '.m4v', '.mp4', '.wmv', '.thm', '.mpg']
        # Scan directory structure to find photos that haven't been uploaded to DB
        count_not_found = 0
       
        for path in paths:
           for root, dirs, files in os.walk(os.path.join(settings.PHOTO_ROOT, path), topdown=True):
               for name in files:
                   if name.endswith('-timelapse') or '-timelapse' in root:
                       continue
                   
                   ignore = False
                   for ext in ignore_extensions:
                       if name.endswith(ext):
                            ignore = True
                   if ignore:
                       continue
                   
                   album = root.replace(settings.PHOTO_ROOT, '') + "/"
                   
                   try:
                       Photo.objects.get(album__name=album, file=name)
                       #print album + name + " " + bcolors.OK + "found" + bcolors.ENDC
                   except Photo.DoesNotExist: 
                       print bcolors.WARNING + album + name  + " " + " NOT FOUND" + bcolors.ENDC
                       count_not_found+=1
                       
        print count_not_found
        
        '''
        # Scan albums in DB to ensure they all exist on file
        albums = Album.objects.all()
        
        for album in albums:
            if os.path.isdir(settings.PHOTO_ROOT + album.name):
                print album.name + " " + bcolors.OK + "found" + bcolors.ENDC
            else:
                print bcolors.WARNING + album.name + " " + " NOT FOUND" + bcolors.ENDC
        '''