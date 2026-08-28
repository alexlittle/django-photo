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
        self.scan_directories_not_in_database()
        self.scan_albums_not_on_disk()

    def report_count(self, counter, problem_message):
        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(problem_message.format(counter)))
        self.stdout.write("---------------------------------------")

    def scan_directories_not_in_database(self):
        """Walk PHOTO_ROOT looking for directories that have no matching Album row."""
        self.stdout.write("Directories not in database")
        self.stdout.write("---------------------------------------")
        counter = 0

        for root, dirs, _files in os.walk(os.path.join(settings.PHOTO_ROOT), topdown=True):
            for name in dirs:
                album_path = (os.path.join(root, name)).replace(settings.PHOTO_ROOT, "") + "/"
                if ignore_folder(album_path):
                    continue

                if not Album.objects.filter(name=album_path).exists():
                    self.stdout.write(self.style.ERROR(f"{album_path} not found"))
                    counter += 1

        self.report_count(counter, "{} directories not in database")

    def scan_albums_not_on_disk(self):
        """Walk every Album row looking for ones whose directory is missing on disk."""
        self.stdout.write("Albums in database but not on disk")
        self.stdout.write("---------------------------------------")
        counter = 0

        for album in Album.objects.all():
            if not os.path.isdir(settings.PHOTO_ROOT + album.name):
                self.stdout.write(self.style.ERROR(f"{album.name} not found"))
                counter += 1

        self.report_count(counter, "{} albums in database but not on disk")
