"""
Management command to find any dirs that haven't been uploaded
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.lib import ignore_folder
from photo.models import Album


class Command(BaseCommand):
    help = "Checks for folders that aren't in the database"

    def handle(self, *args, **options):

        self.stdout.write("Directories not in database")
        self.stdout.write("---------------------------------------")

        # Scan directory structure to find dirs not uploaded to DB
        counter = 0

        for root, dirs, _files in os.walk(os.path.join(settings.PHOTO_ROOT), topdown=True):
            for name in dirs:
                album_path = (os.path.join(root, name)).replace(settings.PHOTO_ROOT, "") + "/"
                if ignore_folder(album_path):
                    continue

                if not Album.objects.filter(name=album_path).exists():
                    self.stdout.write(self.style.ERROR(f"{album_path} not found"))
                    counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} directories not in database"))
        self.stdout.write("---------------------------------------")

        # Scan albums in DB to ensure they all exist on file
        self.stdout.write("Albums in database but not on disk")
        self.stdout.write("---------------------------------------")

        albums = Album.objects.all()
        counter = 0
        for album in albums:
            if not os.path.isdir(settings.PHOTO_ROOT + album.name):
                self.stdout.write(self.style.ERROR(f"{album.name} not found"))
                counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums in database but not on disk"))
        self.stdout.write("---------------------------------------")
