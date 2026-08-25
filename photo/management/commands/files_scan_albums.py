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

        for root, dirs, _files in os.walk(os.path.join(settings.PHOTO_ROOT), topdown=True):
            for name in dirs:
                album_path = (os.path.join(root, name)).replace(settings.PHOTO_ROOT, "") + "/"
                if ignore_folder(album_path):
                    continue

                try:
                    Album.objects.get(name=album_path)
                except Album.DoesNotExist:
                    print(f"{bcolors.WARNING}{album_path} not found{bcolors.ENDC}")
                    counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} directories not in database{bcolors.ENDC}")
        print("---------------------------------------")

        # Scan albums in DB to ensure they all exist on file
        print("Albums in database but not on disk")
        print("---------------------------------------")

        albums = Album.objects.all()
        counter = 0
        for album in albums:
            if not os.path.isdir(settings.PHOTO_ROOT + album.name):
                print(f"{bcolors.WARNING}{album_path} not found{bcolors.ENDC}")
                counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} albums in database but not on disk{bcolors.ENDC}")
        print("---------------------------------------")
