
"""
Management command to find any dirs that haven't been uploaded
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Album


class bcolors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class Command(BaseCommand):
    help = "Checks for folders that aren't in the database"

    def handle(self, *args, **options):

        # Scan directory structure to find dirs not uploaded to DB
        count_not_found = 0

        for root, dirs, files in os.walk(os.path.join(settings.PHOTO_ROOT),
                                         topdown=True):
            for name in dirs:
                if name.endswith('-timelapse') or '-timelapse' in root:
                    continue
                album_path = (os.path.join(root, name)).replace(
                    settings.PHOTO_ROOT, '') + "/"

                if album_path in settings.IGNORE_FOLDERS:
                    continue

                try:
                    Album.objects.get(name=album_path)
                except Album.DoesNotExist:
                    print(bcolors.WARNING + album_path +
                          " " + " NOT FOUND" + bcolors.ENDC)
                    count_not_found += 1

        print(count_not_found)

        # Scan albums in DB to ensure they all exist on file
        albums = Album.objects.all()

        for album in albums:
            if not os.path.isdir(settings.PHOTO_ROOT + album.name):
                print(bcolors.WARNING + album.name +
                      " " + " NOT FOUND" + bcolors.ENDC)
