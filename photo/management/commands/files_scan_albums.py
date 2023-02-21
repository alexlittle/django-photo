
"""
Management command to find any dirs that haven't been uploaded
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.lib import ignore_folder
from photo.models import Album
from . import bcolors

class Command(BaseCommand):
    help = "Checks for folders that aren't in the database"

    def handle(self, *args, **options):

        print("Directories not in database")
        print("---------------------------------------")
        
        # Scan directory structure to find dirs not uploaded to DB
        counter = 0

        for root, dirs, files in os.walk(os.path.join(settings.PHOTO_ROOT), topdown=True):
            for name in dirs:
                album_path = (os.path.join(root, name)).replace(settings.PHOTO_ROOT, '') + "/"

                if ignore_folder(album_path):
                    continue

                try:
                    Album.objects.get(name=album_path)
                except Album.DoesNotExist:
                    print("%s%s not found%s" %(bcolors.WARNING, album_path, bcolors.ENDC))
                    counter += 1

        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d directories not in database%s" % (bcolors.WARNING, counter, bcolors.ENDC))
        print("---------------------------------------")
        
        
        # Scan albums in DB to ensure they all exist on file
        print("Albums in database but not on disk")
        print("---------------------------------------")
        
        albums = Album.objects.all()
        counter = 0
        for album in albums:
            if not os.path.isdir(settings.PHOTO_ROOT + album.name):
                print("%s%s not found%s" %(bcolors.WARNING, album_path, bcolors.ENDC))
                counter += 1
                
        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d albums in database but not on disk%s" % (bcolors.WARNING, counter, bcolors.ENDC))
        print("---------------------------------------")
