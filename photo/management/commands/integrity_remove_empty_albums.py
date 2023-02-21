
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
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d albums with no photos removed %s" % (bcolors.WARNING, counter, bcolors.ENDC))
        print("---------------------------------------")
