"""
Management command to find any photos that haven't been uploaded
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.lib import ignore_file, ignore_folder
from photo.models import Photo

from . import bcolors


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
            print("Photos not uploaded to database")
            print("---------------------------------------")
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

                    dups = []
                    try:
                        Photo.objects.get(album__name=album, file=name)
                        if options["verbose"]:
                            print(f"{album}{name} {bcolors.OK}found{bcolors.ENDC}")
                    except Photo.DoesNotExist:
                        print(f"{album}{name} {bcolors.WARNING} notfound{bcolors.ENDC}")
                        if album not in folders_to_add:
                            folders_to_add.append(album)
                        counter += 1
                    except Photo.MultipleObjectsReturned:
                        dups.append(album + name)

            if counter == 0:
                print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
            else:
                print("---------------------------------------")
                print(f"{bcolors.WARNING}{counter} photos not in database{bcolors.ENDC}")
            print("---------------------------------------")

            print("Multiple copies of photo in database")
            print("---------------------------------------")
            if len(dups) == 0:
                print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
            else:
                print("---------------------------------------")
                print(
                    f"{bcolors.WARNING}{len(dups)} photos with multiple "
                    f"database entries{bcolors.ENDC}"
                )
                print(dups)
            print("---------------------------------------")

        # Scan albums in DB to ensure they all exist on file
        if options["db"]:
            counter = 0
            photos = Photo.objects.all()

            print("Photos in database but not on file")
            print("---------------------------------------")

            for photo in photos:
                if os.path.isfile(settings.PHOTO_ROOT + photo.album.name + photo.file):
                    if options["verbose"]:
                        print(f"{photo.album.name}{photo.file} {bcolors.OK}found{bcolors.ENDC}")
                else:
                    print(
                        f"{bcolors.WARNING}{photo.album.name}{photo.file} not found{bcolors.ENDC}"
                    )
                    if options["autodelete"]:
                        photo.delete()
                        print(bcolors.WARNING + "... DELETED" + bcolors.ENDC)
                    counter += 1

            if counter == 0:
                print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
            else:
                print("---------------------------------------")
                print(
                    f"{bcolors.WARNING}{counter} photos in database but not on file {bcolors.ENDC}"
                )
            print("---------------------------------------")
