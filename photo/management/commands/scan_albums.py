
"""
Management command to find any dirs that haven't been uploaded
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Album

class bcolors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class Command(BaseCommand):
    help = "Checks for folders that aren't in the database"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        paths = ['photos', 'negatives']
       
       
       # Scan directory structure to find dirs that haven't been uploaded to DB
        count_not_found = 0
        ignore = [
                    '/photos/2004/',
                    '/photos/2005/',
                    '/photos/2006/',
                    '/photos/2007/',
                    '/photos/2008/',
                    '/photos/2009/',
                    '/photos/2010/',
                    '/photos/2011/',
                    '/photos/2012/',
                    '/photos/2013/',
                    '/photos/2014/',
                    '/photos/2015/',
                    '/photos/2016/',
                    '/photos/2017/',
                    '/photos/2018/',
                    ]
       
        for path in paths:
           for root, dirs, files in os.walk(os.path.join(settings.PHOTO_ROOT, path), topdown=True):
               for name in dirs:
                   if name.endswith('-timelapse') or '-timelapse' in root:
                       continue
                   album_path = (os.path.join(root, name)).replace(settings.PHOTO_ROOT, '') + "/"
                   
                   if album_path in ignore:
                       continue
                   
                   try:
                       Album.objects.get(name=album_path)
                       #print album_path + " " + bcolors.OK + "found" + bcolors.ENDC
                   except Album.DoesNotExist:
                       print bcolors.WARNING + album_path + " " + " NOT FOUND" + bcolors.ENDC
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