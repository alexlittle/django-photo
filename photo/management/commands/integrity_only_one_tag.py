"""
Management command to find photos with only one tag
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Album, Photo, PhotoTag

from . import bcolors


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        albums = Album.objects.all().order_by("name")
        print("Photos with only one tag")
        print("---------------------------------------")

        counter = 0
        for album in albums:
            photos = Photo.objects.filter(album=album)
            for photo in photos:
                tag_count = PhotoTag.objects.filter(photo=photo).count()
                if tag_count < 2:
                    print(
                        f"{album.name}{photo.file} - {settings.DOMAIN_NAME}/photo/edit/{photo.id}"
                    )
                    counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} photos with only one tag{bcolors.ENDC}")
        print("---------------------------------------")
