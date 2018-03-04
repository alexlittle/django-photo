
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

        # Optional argument to start the summary calculation from the beginning
        parser.add_argument(
            '--filesonly',
            action='store_true',
            dest='filesonly',
            help='Scan files only to check they are in the db',
        )
        
        parser.add_argument(
            '--dbonly',
            action='store_true',
            dest='dbonly',
            help='Scan DB only to check files exist on disk',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='only show items not found',
        )
        
        parser.add_argument(
            '--autodelete',
            action='store_true',
            dest='autodelete',
            help='delete items that are not found',
        )
        

    def handle(self, *args, **options):
        paths = ['photos', 'negatives']
       
        ignore_extensions = ['.avi', '.cr2', '.m4v', '.mp4', '.wmv', '.thm', '.mpg', '.doc', '.xcf']
        # Scan directory structure to find photos that haven't been uploaded to DB
        if options['filesonly']:
        
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
                           if options['verbose']:
                               print album + name + " " + bcolors.OK + "found" + bcolors.ENDC
                       except Photo.DoesNotExist: 
                           print bcolors.WARNING + album + name  + " " + " NOT FOUND" + bcolors.ENDC
                           count_not_found+=1
                           
            print count_not_found
        
        
        # Scan albums in DB to ensure they all exist on file
        if options['dbonly']:
            count_not_found = 0
            photos = Photo.objects.all()
            
            for photo in photos:
                if os.path.isfile(settings.PHOTO_ROOT + photo.album.name + photo.file):
                    if options['verbose']:
                        print photo.album.name + photo.file + " " + bcolors.OK + "found" + bcolors.ENDC
                else:
                    print bcolors.WARNING + photo.album.name + photo.file + " " + " NOT FOUND" + bcolors.ENDC
                    if options['autodelete']:
                        photo.delete()
                        print bcolors.WARNING + "... DELETED" + bcolors.ENDC
                    count_not_found+=1
                    
            print count_not_found
        