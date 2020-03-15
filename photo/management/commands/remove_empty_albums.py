
"""
Management command to clean up any albums with no photos
"""
from django.core.management.base import BaseCommand

from photo.models import Album


class Command(BaseCommand):
    help = "Removes any albums with no photos"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        albums = Album.objects.filter(photo=None)
        for a in albums:
            print("Removing: " + a.name)
            a.delete()
