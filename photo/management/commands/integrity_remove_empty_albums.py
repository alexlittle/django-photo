"""
Management command to clean up any albums with no photos
"""

from django.core.management.base import BaseCommand

from photo.models import Album


class Command(BaseCommand):
    help = "Removes any albums with no photos"

    def handle(self, *args, **options):
        albums = Album.objects.filter(photo=None)

        self.stdout.write("Albums with no photos")
        self.stdout.write("---------------------------------------")
        counter = albums.count()

        for a in albums:
            self.stdout.write("Removing: " + a.name)
            a.delete()

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums with no photos removed"))
        self.stdout.write("---------------------------------------")
