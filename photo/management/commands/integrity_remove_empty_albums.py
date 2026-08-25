"""
Management command to clean up any albums with no photos
"""

from django.core.management.base import BaseCommand

from photo.models import Album

from . import bcolors


class Command(BaseCommand):
    help = "Removes any albums with no photos"

    def handle(self, *args, **options):
        albums = Album.objects.filter(photo=None)

        print("Albums with no photos")
        print("---------------------------------------")
        counter = albums.count()

        for a in albums:
            print("Removing: " + a.name)
            a.delete()

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} albums with no photos removed {bcolors.ENDC}")
        print("---------------------------------------")
