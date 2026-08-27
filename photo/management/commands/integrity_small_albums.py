"""
Management command to find albums with less than X photos
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Album


class Command(BaseCommand):
    help = "Finds albums with less than X photos"

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--count",
            dest="max_count",
            help="max_count",
        )

    def handle(self, *args, **options):
        max_count = int(options["max_count"])

        self.stdout.write(f"Albums with less than {max_count} photos")
        self.stdout.write("---------------------------------------")
        counter = 0

        for album in Album.objects.annotate(total=Count("photo")):
            if album.total < max_count:
                link = f"{settings.DOMAIN_NAME}/album/{album.id}"
                self.stdout.write(f"{link} - {album.title} - {album.name} [{album.total} photos]")
                counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(
                self.style.WARNING(f"{counter} albums with less than {max_count} photos")
            )
        self.stdout.write("---------------------------------------")
