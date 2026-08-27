"""
Management command to find photos with only one tag
"""

from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.lib import get_domain
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
                tag_count = PhotoTag.objects.filter(photo=photo).values("tag").distinct().count()
                if tag_count < 2:
                    link = reverse("photo:edit", args=(photo.id,))
                    self.stdout.write(f"{album.name}{photo.file} - {get_domain()}{link}")
                    counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} photos with only one tag"))
        self.stdout.write("---------------------------------------")
