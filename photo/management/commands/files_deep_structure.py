"""
Management command to find albums with deep directory structure
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Album

from . import bcolors


class Command(BaseCommand):
    help = "Finds albums with deep directory structure"

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--count",
            dest="max_dirs",
            help="max_dirs",
        )

    def handle(self, *args, **options):
        max_dirs = int(options["max_dirs"])
        print(f"Finds albums deeper than {max_dirs} directories")
        print("---------------------------------------")
        counter = 0
        for album in Album.objects.all():
            dirs = filter(None, album.name.split("/"))
            if len(list(dirs)) > max_dirs:
                print(f"{settings.DOMAIN_NAME}album/{album.id} - {album.title} [{album.name}]")
                counter += 1
        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} directories deeper than {max_dirs}{bcolors.ENDC}")
        print("---------------------------------------")
