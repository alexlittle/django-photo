"""
Management command to find any photos that haven't been uploaded
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

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

    def handle(self, *args, **options):
        if not options["files"] and not options["db"]:
            raise CommandError("Nothing to do: pass --files and/or --db")

        if options["files"]:
            self.scan_files_not_in_database(verbose=options["verbose"])

        if options["db"]:
            self.scan_database_not_on_disk(
                verbose=options["verbose"], autodelete=options["autodelete"]
            )

    def report_count(self, counter, problem_message):
        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(problem_message.format(counter)))
        self.stdout.write("---------------------------------------")

    def find_photo_on_disk(self, root, name, verbose):
        """Report on a single on-disk file, returning True if it is missing from the DB."""
        album = root.replace(settings.PHOTO_ROOT, "") + "/"
        try:
            Photo.objects.get(album__name=album, file=name)
            if verbose:
                self.stdout.write(f"{album}{name} " + self.style.SUCCESS("found"))
            return None
        except Photo.DoesNotExist:
            self.stdout.write(f"{album}{name} " + self.style.ERROR("notfound"))
            return album

    def scan_files_not_in_database(self, verbose):
        """Walk PHOTO_ROOT looking for files that have no matching Photo row."""
        self.stdout.write("Photos not uploaded to database")
        self.stdout.write("---------------------------------------")
        counter = 0

        for root, dirs, files in os.walk(settings.PHOTO_ROOT, topdown=True):
            if ignore_folder(root):
                dirs[:] = []
                continue
            for name in files:
                if ignore_file(name):
                    continue
                if self.find_photo_on_disk(root, name, verbose) is not None:
                    counter += 1

        self.report_count(counter, "{} photos not in database")

        self.stdout.write("Multiple copies of photo in database")
        self.stdout.write("---------------------------------------")
        # Photo.file is unique=True at the model level, so a photo can
        # never have more than one database entry.
        self.stdout.write(self.style.SUCCESS("OK"))
        self.stdout.write("---------------------------------------")

    def check_photo_on_disk(self, photo, verbose, autodelete):
        """Report on a single Photo row, returning True if its file is missing."""
        if os.path.isfile(settings.PHOTO_ROOT + photo.album.name + photo.file):
            if verbose:
                self.stdout.write(f"{photo.album.name}{photo.file} " + self.style.SUCCESS("found"))
            return False

        self.stdout.write(self.style.ERROR(f"{photo.album.name}{photo.file} not found"))
        if autodelete:
            photo.delete()
            self.stdout.write(self.style.WARNING("... DELETED"))
        return True

    def scan_database_not_on_disk(self, verbose, autodelete):
        """Walk every Photo row looking for ones whose file is missing on disk."""
        counter = 0

        self.stdout.write("Photos in database but not on file")
        self.stdout.write("---------------------------------------")

        for photo in Photo.objects.select_related("album").all():
            if self.check_photo_on_disk(photo, verbose, autodelete):
                counter += 1

        self.report_count(counter, "{} photos in database but not on file")
