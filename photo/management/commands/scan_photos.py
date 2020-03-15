
"""
Management command to find any photos that haven't been uploaded
"""
import os

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from photo.models import Photo
from photo.views import upload_album


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
            '--files',
            action='store_true',
            dest='files',
            help='Scan files only to check they are in the db',
        )

        parser.add_argument(
            '--db',
            action='store_true',
            dest='db',
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

        parser.add_argument(
            '--autoadd',
            action='store_true',
            dest='autoadd',
            help='add items that are not found',
        )

    def handle(self, *args, **options):

        ignore_extensions = ['.avi', '.cr2', '.m4v', '.mp4', '.wmv',
                             '.thm', '.mpg', '.doc', '.xcf', 'pdf',
                             '.heic', '.mov', '.mkv']
        # Scan directory structure to find photos not uploaded to DB
        if options['files']:

            count_not_found = 0
            folders_to_add = []

            for root, dirs, files in os.walk(settings.PHOTO_ROOT,
                                             topdown=True):
                for name in files:
                    if name.endswith('-timelapse') or '-timelapse' in root:
                        continue

                    ignore = False
                    for ext in ignore_extensions:
                        if name.lower().endswith(ext):
                            ignore = True
                    if ignore:
                        continue

                    album = root.replace(settings.PHOTO_ROOT, '') + "/"

                    try:
                        if options['verbose']:
                            print("checking..." + album + name)
                        Photo.objects.get(album__name=album, file=name)
                        if options['verbose']:
                            print(album + name + " " + bcolors.OK +
                                  "found" + bcolors.ENDC)
                    except Photo.DoesNotExist:
                        print(bcolors.WARNING + album + name +
                              " " + " NOT FOUND" + bcolors.ENDC)
                        if album not in folders_to_add:
                            folders_to_add.append(album)
                        count_not_found += 1

            print(count_not_found)

            if options['autoadd']:
                for folder in folders_to_add:
                    print(folder)
                    default_tags = input("Enter the default tags...")
                    print(default_tags)
                    upload_album(folder, default_tags, timezone.now())

        # Scan albums in DB to ensure they all exist on file
        if options['db']:
            count_not_found = 0
            photos = Photo.objects.all()

            for photo in photos:
                if os.path.isfile(settings.PHOTO_ROOT
                                  + photo.album.name
                                  + photo.file):
                    if options['verbose']:
                        print(photo.album.name + photo.file + " " +
                              bcolors.OK + "found" + bcolors.ENDC)
                else:
                    print(bcolors.WARNING + photo.album.name +
                          photo.file + " " + " NOT FOUND" + bcolors.ENDC)
                    if options['autodelete']:
                        photo.delete()
                        print(bcolors.WARNING + "... DELETED" + bcolors.ENDC)
                    count_not_found += 1

            print(count_not_found)
