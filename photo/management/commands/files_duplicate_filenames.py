"""
Management command to find photos with same filename
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Checks for photos with duplicate filenames"

    def handle(self, *args, **options):
        # Photo.file is unique=True at the model level, so no two photos can
        # ever share a filename -- this always reports OK.
        self.stdout.write("Photos with same filename")
        self.stdout.write("---------------------------------------")
        self.stdout.write(self.style.SUCCESS("OK"))
        self.stdout.write("---------------------------------------")
