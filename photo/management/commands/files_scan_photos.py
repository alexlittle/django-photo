"""
Management command to find any photos that haven't been uploaded
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.lib import ignore_file, ignore_folder
from photo.models import Photo


class Command(BaseCommand):
    help = "Checks for photos that aren't in the database"

    def add_arguments(self, parser):

        # Optional argument to start the summary calculation from the beginning
        parser.add_argument(
            "--files",
            action="store_true",
            dest="files",
            help="Scan files only to check they are in the db",
        )

        parser.add_argument(
            "--db",
            action="store_true",
            dest="db",
            help="Scan DB only to check files exist on disk",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            dest="verbose",
            help="only show items not found",
        )

        parser.add_argument(
            "--autodelete",
            action="store_true",
            dest="autodelete",
            help="delete items that are not found",
        )

        parser.add_argument(
            "--autoadd",
            action="store_true",
            dest="autoadd",
            help="add items that are not found",
        )

    def handle(self, *args, **options):

        # Scan directory structure to find photos not uploaded to DB
        if options["files"]:
            self.stdout.write("Photos not uploaded to database")
            self.stdout.write("---------------------------------------")
            counter = 0
            folders_to_add = []

            for root, dirs, files in os.walk(settings.PHOTO_ROOT, topdown=True):
                if ignore_folder(root):
                    dirs[:] = []
                    continue
                for name in files:
                    if ignore_file(name):
                        continue

                    album = root.replace(settings.PHOTO_ROOT, "") + "/"

                    try:
                        Photo.objects.get(album__name=album, file=name)
                        if options["verbose"]:
                            self.stdout.write(f"{album}{name} " + self.style.SUCCESS("found"))
                    except Photo.DoesNotExist:
                        self.stdout.write(f"{album}{name} " + self.style.ERROR("notfound"))
                        if album not in folders_to_add:
                            folders_to_add.append(album)
                        counter += 1

            if counter == 0:
                self.stdout.write(self.style.SUCCESS("OK"))
            else:
                self.stdout.write("---------------------------------------")
                self.stdout.write(self.style.WARNING(f"{counter} photos not in database"))
            self.stdout.write("---------------------------------------")

            self.stdout.write("Multiple copies of photo in database")
            self.stdout.write("---------------------------------------")
            # Photo.file is unique=True at the model level, so a photo can
            # never have more than one database entry.
            self.stdout.write(self.style.SUCCESS("OK"))
            self.stdout.write("---------------------------------------")

        # Scan albums in DB to ensure they all exist on file
        if options["db"]:
            counter = 0
            photos = Photo.objects.all()

            self.stdout.write("Photos in database but not on file")
            self.stdout.write("---------------------------------------")

            for photo in photos:
                if os.path.isfile(settings.PHOTO_ROOT + photo.album.name + photo.file):
                    if options["verbose"]:
                        self.stdout.write(
                            f"{photo.album.name}{photo.file} " + self.style.SUCCESS("found")
                        )
                else:
                    self.stdout.write(self.style.ERROR(f"{photo.album.name}{photo.file} not found"))
                    if options["autodelete"]:
                        photo.delete()
                        self.stdout.write(self.style.WARNING("... DELETED"))
                    counter += 1

            if counter == 0:
                self.stdout.write(self.style.SUCCESS("OK"))
            else:
                self.stdout.write("---------------------------------------")
                self.stdout.write(
                    self.style.WARNING(f"{counter} photos in database but not on file")
                )
            self.stdout.write("---------------------------------------")
