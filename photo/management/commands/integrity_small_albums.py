"""
Management command to find albums with less than X photos
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Album

from . import bcolors


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

        print(f"Albums with less than {max_count} photos")
        print("---------------------------------------")
        counter = 0

        for album in Album.objects.annotate(total=Count("photo")):
            if album.total < max_count:
                link = f"{settings.DOMAIN_NAME}/album/{album.id}"
                print(f"{link} - {album.title} - {album.name} [{album.total} photos]")
                counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(
                f"{bcolors.WARNING}{counter} albums with less than "
                f"{max_count} photos {bcolors.ENDC}"
            )
        print("---------------------------------------")
