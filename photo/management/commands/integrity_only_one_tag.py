"""
Management command to find photos with only one tag
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Album, Photo, PhotoTag


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        albums = Album.objects.all().order_by("name")
        self.stdout.write("Photos with only one tag")
        self.stdout.write("---------------------------------------")

        counter = 0
        for album in albums:
            photos = Photo.objects.filter(album=album)
            for photo in photos:
                tag_count = PhotoTag.objects.filter(photo=photo).count()
                if tag_count < 2:
                    self.stdout.write(
                        f"{album.name}{photo.file} - {settings.DOMAIN_NAME}/photo/edit/{photo.id}"
                    )
                    counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} photos with only one tag"))
        self.stdout.write("---------------------------------------")
