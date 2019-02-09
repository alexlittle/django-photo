
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
       
       # Scan directory structure to find dirs that haven't been uploaded to DB
        count_not_found = 0
        ignore = [
                    '/2004/',
                    '/2005/',
                    '/2006/',
                    '/2007/',
                    '/2008/',
                    '/2008/2008-05-ledbury/',
                    '/2008/08/',
                    '/2008/2008-08-leaving-ou/',
                    '/2008/09/',
                    '/2008/10/',
                    '/2008/11/',
                    '/2008/12/',
                    '/2008/12/gheralta/',
                    '/2009/',
                    '/2009/01/danakil/',
                    '/2009/01/',
                    '/2009/02/',
                    '/2009/02/simiens/',
                    '/2009/02/simiens/360/',
                    '/2009/03/',
                    '/2009/04/',
                    '/2009/05/',
                    '/2010/',
                    '/2011/',
                    '/2012/',
                    '/2012/2012-05-31-hew-video/',
                    '/2013/',
                    '/2014/',
                    '/2015/',
                    '/2016/',
                    '/2017/',
                    '/2018/',
                    '/albums/',
                    '/negatives/',
                    ]
       
        
        for root, dirs, files in os.walk(os.path.join(settings.PHOTO_ROOT), topdown=True):
           for name in dirs:
               if name.endswith('-timelapse') or '-timelapse' in root:
                   continue
               album_path = (os.path.join(root, name)).replace(settings.PHOTO_ROOT, '') + "/"
               
               if album_path in ignore:
                   continue
               
               try:
                   Album.objects.get(name=album_path)
                   #print(album_path + " " + bcolors.OK + "found" + bcolors.ENDC)
               except Album.DoesNotExist:
                   print(bcolors.WARNING + album_path + " " + " NOT FOUND" + bcolors.ENDC)
                   count_not_found+=1
                       
        print(count_not_found)
        
        
        # Scan albums in DB to ensure they all exist on file
        albums = Album.objects.all()
        
        for album in albums:
            if os.path.isdir(settings.PHOTO_ROOT + album.name):
                #print(album.name + " " + bcolors.OK + "found" + bcolors.ENDC)
                pass
            else:
                print(bcolors.WARNING + album.name + " " + " NOT FOUND" + bcolors.ENDC)
        